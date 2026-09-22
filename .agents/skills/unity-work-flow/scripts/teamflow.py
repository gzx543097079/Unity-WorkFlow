#!/usr/bin/env python3
"""unity-work-flow：需求、验证、提交检查与显式发布动作记录。"""
import argparse
import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MARKER = '<!-- teamflow:requirement:vnext -->'
REQ_ID = re.compile(r'REQ-(\d{4})')
STATE_ICONS = {'待处理': '⚪', '待确认': '🟡', '进行中': '🔵', '待用户验证': '🟣',
               '完成': '✅', '阻塞': '🔴', '暂停': '🟠', '取消': '⚫'}
STATES = tuple(STATE_ICONS)
OPERATIONS = ('export-xcode', 'archive', 'upload-testflight', 'distribute-testflight',
              'submit-beta-review', 'submit-app-review', 'publish', 'phased-release',
              'pause-phased-release', 'remove-sale')
OPERATION_NAMES = {'export-xcode': '导出 Xcode 工程', 'archive': 'Archive',
                   'upload-testflight': '上传 TestFlight', 'distribute-testflight': '分发 TestFlight',
                   'submit-beta-review': '提交 Beta App Review',
                   'submit-app-review': '提交 App Store 审核', 'publish': '发布 App Store 版本',
                   'phased-release': '开启分阶段发布', 'pause-phased-release': '暂停分阶段发布',
                   'remove-sale': '下架'}


def safe(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('路径必须位于项目内：' + str(name))
    for node in (path, *path.parents):
        if node == root:
            break
        if node.is_symlink():
            raise ValueError('路径不能包含符号链接：' + str(name))
    return path


def state_display(state):
    return STATE_ICONS[state] + ' ' + state


def progress_display(done, total):
    return ('✅' if done == total else '🔵' if done else '⚪') + f' {done}/{total}'


def field(text, name):
    values = re.findall(r'^- ' + re.escape(name) + r'：(.+)$', text, re.M)
    if len(values) != 1 or not values[0].strip():
        raise ValueError('需求卡必须且只能填写一处：' + name)
    return values[0].strip()


def requirement_path(root, requirement):
    if not REQ_ID.fullmatch(requirement):
        raise ValueError('需求编号格式应为 REQ-0001')
    path = safe(root, 'requirements/' + requirement + '.md')
    if not path.is_file():
        raise ValueError('需求不存在：' + requirement)
    return path


def parse_card(path):
    text = path.read_text()
    if MARKER not in text:
        raise ValueError('只支持当前格式需求卡：' + path.name)
    state_value = field(text, '状态')
    state = next((name for name in STATES if state_value == state_display(name)), None)
    if not state:
        raise ValueError('需求状态无效：' + state_value)
    scope, excluded = field(text, '范围'), field(text, '不包含')
    if scope in ('待填写', '—') or excluded in ('待填写', '—'):
        raise ValueError('范围和不包含必须填写实际内容')
    ac = []
    for line in text.splitlines():
        match = re.match(r'^- (⚪|✅) (AC-\d+)：(.+)$', line)
        if match:
            ac.append({'id': match.group(2), 'done': match.group(1) == '✅',
                       'condition': match.group(3).strip()})
    if not ac or len({item['id'] for item in ac}) != len(ac):
        raise ValueError('需求卡必须包含不重复的 AC 项')
    done = sum(item['done'] for item in ac)
    return {'requirement': path.stem, 'state': state, 'state_display': state_display(state),
            'progress': {'done': done, 'total': len(ac), 'display': progress_display(done, len(ac))},
            'scope': scope, 'excluded': excluded, 'ac': ac, 'text': text}


def cards(root):
    directory = safe(root, 'requirements')
    if not directory.exists():
        return []
    rows = []
    for path in directory.glob('REQ-*.md'):
        if not REQ_ID.fullmatch(path.stem):
            continue
        try:
            card = parse_card(path)
        except (OSError, ValueError) as error:
            print('已跳过异常需求卡 ' + path.name + '：' + str(error), file=sys.stderr)
            continue
        title = next((line[2:].removeprefix(path.stem + '：') for line in card['text'].splitlines()
                      if line.startswith('# ')), path.stem)
        rows.append({'requirement': path.stem, 'title': title, 'state': card['state_display'],
                     'state_key': card['state'], 'progress': card['progress']})
    return sorted(rows, key=lambda row: int(REQ_ID.fullmatch(row['requirement']).group(1)))


def create(root, title, queued=False, bug=False):
    if not title.strip() or '\n' in title or '\r' in title:
        raise ValueError('标题须为单行非空文本')
    directory = safe(root, 'requirements')
    directory.mkdir(parents=True, exist_ok=True)
    numbers = [int(REQ_ID.fullmatch(path.stem).group(1)) for path in directory.glob('REQ-*.md')
               if REQ_ID.fullmatch(path.stem)]
    for number in range(max(numbers, default=0) + 1, 10000):
        requirement = f'REQ-{number:04d}'
        target = directory / (requirement + '.md')
        template = Path(__file__).resolve().parents[1] / 'references/templates' / ('bug-fix.md' if bug else 'requirement.md')
        content = template.read_text().replace('REQ-0000', requirement).replace('〈需求标题〉', title.strip())
        if queued:
            content = content.replace('- 状态：' + state_display('进行中'), '- 状态：' + state_display('待处理'), 1)
        try:
            with target.open('x') as stream:
                stream.write(content)
        except FileExistsError:
            continue
        result = {'requirement': requirement, 'card': str(target)}
        print(json.dumps(result, ensure_ascii=False))
        return result
    raise ValueError('需求编号已用尽')


def replace_field(text, name, value):
    pattern = r'^- ' + re.escape(name) + r'：.*$'
    if len(re.findall(pattern, text, re.M)) != 1:
        raise ValueError('需求卡字段缺失或重复：' + name)
    return re.sub(pattern, '- ' + name + '：' + value, text, count=1, flags=re.M)


def set_state(root, requirement, state, reason=None):
    if state in ('待确认', '阻塞', '暂停', '取消') and not (reason and reason.strip()):
        raise ValueError(state + ' 必须填写原因或恢复条件')
    path = requirement_path(root, requirement)
    card = parse_card(path)
    text = replace_field(card['text'], '状态', state_display(state))
    if reason and reason.strip():
        heading = '## 决策与异常'
        entry = f'- {datetime.now(timezone.utc).isoformat()}：{state_display(state)} — {reason.strip()}'
        text = text.rstrip() + ('\n\n' + heading + '\n\n' if heading not in text else '\n') + entry + '\n'
    path.write_text(text)
    print(json.dumps({'requirement': requirement, 'state': state_display(state),
                      'state_key': state}, ensure_ascii=False))


def checks_module():
    source = Path(__file__).with_name('project_checks.py')
    spec = importlib.util.spec_from_file_location('teamflow_project_checks', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete(root, requirement, result=None, evidence=None, wait_user=False):
    if bool(result) == bool(evidence):
        raise ValueError('完成需求时必须且只能提供 --result 或 --evidence')
    path = requirement_path(root, requirement)
    card = parse_card(path)
    pending = [item['id'] for item in card['ac'] if not item['done']]
    if pending:
        raise ValueError('仍有未完成 AC：' + ', '.join(pending))
    if result:
        with contextlib.redirect_stdout(io.StringIO()):
            report = checks_module().verify(root, result)
        proof = result + '（' + report['profile'] + '，通过）'
    else:
        proof = evidence.strip()
        if not proof:
            raise ValueError('验证证据不能为空')
    target_state = '待用户验证' if wait_user else '完成'
    text = replace_field(card['text'], '状态', state_display(target_state))
    text = replace_field(text, '验证状态', '🟣 待用户验证' if wait_user else '✅ 通过')
    text = replace_field(text, '验证证据', proof)
    path.write_text(text)
    print(json.dumps({'requirement': requirement, 'state': state_display(target_state),
                      'state_key': target_state, 'evidence': proof}, ensure_ascii=False))


def git_check(root, requirement, result=None, evidence=None):
    top = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], text=True).strip()
    if Path(top).resolve() != root:
        raise ValueError('请从项目 Git 根目录执行')
    card = parse_card(requirement_path(root, requirement))
    if card['state'] not in ('完成', '待用户验证'):
        raise ValueError('只有完成或待用户验证的需求可以进入提交检查')
    names = [name for name in subprocess.check_output(
        ['git', '-C', str(root), 'diff', '--cached', '--name-only', '-z']).decode().split('\0') if name]
    if not names:
        raise ValueError('暂存区为空')
    if bool(result) == bool(evidence):
        raise ValueError('提交检查必须且只能提供 --result 或 --evidence')
    if result:
        with contextlib.redirect_stdout(io.StringIO()):
            checks_module().verify(root, result, staged=True)
        proof = result
    else:
        proof = evidence.strip()
        if not proof:
            raise ValueError('提交检查证据不能为空')
    risky_suffixes = ('.cs', '.asmdef', '.asmref', '.unity', '.prefab', '.asset', '.meta', '.shader',
                      '.compute', '.json', '.plist', '.entitlements', '.pbxproj', '.xcconfig', '.mm', '.m', '.h')
    risky = [name for name in names if Path(name).suffix.lower() in risky_suffixes
             or name.startswith(('Packages/', 'ProjectSettings/'))]
    print(json.dumps({'requirement': requirement, 'staged_files': names, 'validation': proof,
                      'semantic_review_required': True, 'unity_sensitive_files': risky,
                      'commit_trailer': 'Requirement: ' + requirement}, ensure_ascii=False, indent=2))


def release_options(operation, internal_only=False):
    if internal_only and operation != 'upload-testflight':
        raise ValueError('TestFlight Internal Only 仅适用于上传 TestFlight')
    return {'testFlightInternalTestingOnly': True} if internal_only else {}


def release_prepare(operation, version, build, internal_only=False):
    print(json.dumps({'mode': 'read-only', 'operation': operation,
                      'display_name': OPERATION_NAMES[operation], 'version': version, 'build': build,
                      'external_write': False, 'export_options_overrides': release_options(operation, internal_only),
                      'message': '只准备并核对该动作；不得执行相邻或后续发布动作。'},
                     ensure_ascii=False, indent=2))


def release_record(root, operation, version, build, evidence, internal_only=False):
    if not evidence.strip() or not version.strip() or not build.strip():
        raise ValueError('版本、build 和真实证据不能为空')
    release_options(operation, internal_only)
    directory = safe(root, 'releases')
    directory.mkdir(parents=True, exist_ok=True)
    clean_version = re.sub(r'[^A-Za-z0-9._-]', '-', version)
    clean_build = re.sub(r'[^A-Za-z0-9._-]', '-', build)
    path = directory / f'Unity-iOS-{clean_version}-{clean_build}.md'
    text = path.read_text() if path.exists() else f'# Unity iOS 发布动作：{version} / {build}\n'
    display = OPERATION_NAMES[operation] + ('（TestFlight Internal Only）' if internal_only else '')
    entry = f'- {datetime.now(timezone.utc).isoformat()} | {display} | {evidence.strip()}\n'
    path.write_text(text.rstrip() + '\n\n' + entry)
    print(json.dumps({'record': str(path), 'operation': operation}, ensure_ascii=False))


def list_output(root, as_json=False):
    rows = cards(root)
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    lines = ['| 需求 | 标题 | 状态 | 进度 |', '| --- | --- | --- | --- |']
    lines.extend(f"| [{row['requirement']}](requirements/{row['requirement']}.md) | {row['title']} | {row['state']} | {row['progress']['display']} |" for row in rows)
    print('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('.'))
    top = parser.add_subparsers(dest='area', required=True)
    req = top.add_parser('req')
    req_sub = req.add_subparsers(dest='command', required=True)
    creator = req_sub.add_parser('create')
    creator.add_argument('--title', required=True)
    creator.add_argument('--queued', action='store_true')
    creator.add_argument('--bug', action='store_true')
    listing = req_sub.add_parser('list')
    listing.add_argument('--json', action='store_true')
    status = req_sub.add_parser('status')
    status.add_argument('requirement')
    state = req_sub.add_parser('state')
    state.add_argument('requirement')
    state.add_argument('--state', choices=STATES, required=True)
    state.add_argument('--reason')
    done = req_sub.add_parser('complete')
    done.add_argument('requirement')
    done.add_argument('--result')
    done.add_argument('--evidence')
    done.add_argument('--wait-user', action='store_true')
    verify_area = top.add_parser('verify')
    verify_sub = verify_area.add_subparsers(dest='command', required=True)
    verify_sub.add_parser('list')
    run_parser = verify_sub.add_parser('run')
    run_parser.add_argument('--profile', required=True)
    git_area = top.add_parser('git')
    git_sub = git_area.add_subparsers(dest='command', required=True)
    check = git_sub.add_parser('check')
    check.add_argument('requirement')
    check.add_argument('--result')
    check.add_argument('--evidence')
    release = top.add_parser('release')
    release_sub = release.add_subparsers(dest='command', required=True)
    for command in ('prepare', 'record'):
        action = release_sub.add_parser(command)
        action.add_argument('operation', choices=OPERATIONS)
        action.add_argument('--version', required=True)
        action.add_argument('--build', required=True)
        action.add_argument('--testflight-internal-only', action='store_true')
        if command == 'record':
            action.add_argument('--evidence', required=True)
    args = parser.parse_args()
    root = args.project.resolve()
    try:
        if args.area == 'req':
            if args.command == 'create':
                create(root, args.title, args.queued, args.bug)
            elif args.command == 'list':
                list_output(root, args.json)
            elif args.command == 'status':
                card = parse_card(requirement_path(root, args.requirement))
                payload = {key: value for key, value in card.items() if key not in ('text', 'state_display')}
                payload['state_key'], payload['state'] = payload['state'], card['state_display']
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            elif args.command == 'state':
                set_state(root, args.requirement, args.state, args.reason)
            else:
                complete(root, args.requirement, args.result, args.evidence, args.wait_user)
        elif args.area == 'verify':
            checks = checks_module()
            if args.command == 'list':
                print(json.dumps(checks.load_config(root), ensure_ascii=False, indent=2))
            else:
                return 0 if checks.run(root, args.profile)[1] else 1
        elif args.area == 'git':
            git_check(root, args.requirement, args.result, args.evidence)
        elif args.command == 'prepare':
            release_prepare(args.operation, args.version, args.build, args.testflight_internal_only)
        else:
            release_record(root, args.operation, args.version, args.build, args.evidence,
                           args.testflight_internal_only)
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(2, str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
