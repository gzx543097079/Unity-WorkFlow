#!/usr/bin/env python3
"""执行项目声明的验证命令，并把结果绑定到不可变输入指纹。"""
import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

CONFIG = '.agents/project-checks.json'
EVIDENCE_DIRS = ('logs/', 'releases/', '.agents/teamflow-backups/')
GENERATED_PARTS = {'.git', '__pycache__', 'Library', 'Temp', 'Obj', 'Logs', 'UserSettings',
                   'MemoryCaptures', 'Recordings', 'DerivedData'}


def local_path(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('路径必须位于项目内：' + str(name))
    for node in (path, *path.parents):
        if node == root:
            break
        if node.is_symlink():
            raise ValueError('路径不能含符号链接：' + str(name))
    return path


def load_config(root):
    config = json.loads(local_path(root, CONFIG).read_text())
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise ValueError('配置 schema_version 必须为 1')
    checks, profiles = config.get('checks'), config.get('profiles')
    if not isinstance(checks, dict) or not isinstance(profiles, dict):
        raise ValueError('checks 和 profiles 必须为对象')
    for name, check in checks.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name) or not isinstance(check, dict):
            raise ValueError('检查名称或配置无效')
        argv = check.get('argv')
        if (not isinstance(argv, list) or not argv
                or any(not isinstance(arg, str) or not arg or '\0' in arg for arg in argv)):
            raise ValueError(name + ' 的 argv 必须为非空字符串数组')
        timeout = check.get('timeout_seconds', 900)
        if type(timeout) is not int or not 1 <= timeout <= 86400:
            raise ValueError(name + ' 的 timeout_seconds 必须为 1–86400')
        if not local_path(root, check.get('cwd', '.')).is_dir():
            raise ValueError(name + ' 的工作目录不存在')
    for name, selected in profiles.items():
        if (not re.fullmatch(r'[A-Za-z0-9_-]+', name) or not isinstance(selected, list)
                or not selected or len(selected) != len(set(selected))
                or any(item not in checks for item in selected)):
            raise ValueError('profile 必须包含不重复的有效检查：' + str(name))
    overrides = config.get('profile_inputs', {})
    if not isinstance(overrides, dict) or any(name not in profiles for name in overrides):
        raise ValueError('profile_inputs 必须引用已配置的 profile')
    return config


def excluded_input(name):
    parts = Path(name).parts
    return (name.startswith(EVIDENCE_DIRS) or any(part in GENERATED_PARTS for part in parts)
            or any(part.endswith('.xcresult') for part in parts)
            or Path(name).suffix in ('.pyc', '.pyo', '.ipa'))


def input_paths(root, inputs=None, candidates=None):
    if inputs is not None:
        if (not isinstance(inputs, list) or not inputs
                or any(not isinstance(item, str) or not item for item in inputs)):
            raise ValueError('inputs 必须是非空项目相对文件/目录列表')
        for item in inputs:
            local_path(root, item)
        inputs = [str(Path(item)) for item in inputs]
    validate_inputs = candidates is None
    if candidates is None:
        try:
            raw = subprocess.check_output(
                ['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                stderr=subprocess.PIPE)
            candidates = {os.fsdecode(item) for item in raw.split(b'\0') if item}
        except subprocess.CalledProcessError:
            if inputs is None:
                raise ValueError('非 Git 项目必须显式配置 inputs')
            candidates = set()
            for item in inputs:
                path = local_path(root, item)
                paths = [path] if not path.is_dir() else path.rglob('*')
                candidates.update(str(p.relative_to(root)) for p in paths if p.is_file() or p.is_symlink())
    if validate_inputs and inputs is not None:
        for item in inputs:
            if any(not excluded_input(name) and (item == '.' or name == item or name.startswith(item + '/'))
                   for name in candidates):
                continue
            history = subprocess.run(['git', '-C', str(root), 'log', '-1', '--format=%H', '--', item],
                                     capture_output=True, text=True)
            if history.returncode != 0 or not history.stdout.strip():
                raise ValueError('验证输入无有效文件且无跟踪历史：' + item)
    return {name for name in candidates if not excluded_input(name) and
            (inputs is None or any(item == '.' or name == item or name.startswith(item.rstrip('/') + '/')
                                   for item in inputs))}


def normalized_content(name, content):
    """需求卡状态和证据可在验证后更新，不令已验证范围自失效。"""
    if not (name.startswith('requirements/REQ-') and name.endswith('.md')):
        return content
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        return content
    if '<!-- teamflow:requirement:vnext -->' not in text:
        return content
    output, ignored = [], False
    for line in text.splitlines():
        if line.startswith('## '):
            ignored = line in ('## 验证', '## 决策与异常')
        if ignored or line.startswith('- 状态：'):
            continue
        match = re.match(r'^- (?:⚪|✅) (AC-\d+：.+)$', line)
        output.append('- ' + match.group(1) if match else line)
    return ('\n'.join(output) + '\n').encode()


def source_snapshot(root, config, profile=None, staged=False):
    inputs = config.get('profile_inputs', {}).get(profile, config.get('inputs'))
    index = {}
    if staged:
        raw = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--stage', '-z'],
                                      stderr=subprocess.PIPE)
        for entry in filter(None, raw.split(b'\0')):
            metadata, raw_name = entry.split(b'\t', 1)
            mode, oid, stage = metadata.split()
            if stage != b'0':
                raise ValueError('暂存区有未解决冲突')
            index[os.fsdecode(raw_name)] = (mode, oid)
    paths = input_paths(root, inputs)
    if staged:
        paths.update(input_paths(root, inputs, index))
    paths.add(CONFIG)
    files = {}
    for name in sorted(paths):
        if excluded_input(name):
            continue
        if inputs is None and name.startswith('requirements/') and name.endswith('.md'):
            continue
        if staged:
            entry = index.get(name)
            if entry is None:
                continue
            mode, oid = entry
            if mode not in (b'100644', b'100755'):
                raise ValueError('暂存输入不是普通文件：' + name)
            content = subprocess.check_output(['git', '-C', str(root), 'cat-file', 'blob', oid.decode()],
                                              stderr=subprocess.PIPE)
            files[name] = {'sha256': hashlib.sha256(normalized_content(name, content)).hexdigest(),
                           'executable': mode == b'100755'}
            continue
        path = local_path(root, name)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError('输入不是普通文件：' + name)
        files[name] = {'sha256': hashlib.sha256(normalized_content(name, path.read_bytes())).hexdigest(),
                       'executable': bool(path.stat().st_mode & 0o111)}
    encoded = json.dumps(files, sort_keys=True, ensure_ascii=True).encode()
    return {'algorithm': 'sha256-files-v3',
            'fingerprint': hashlib.sha256(encoded).hexdigest(), 'files': files}


def verify(root, result, staged=False):
    root = root.resolve()
    report = json.loads(local_path(root, result).read_text())
    if (not isinstance(report, dict) or report.get('status') != '通过'
            or not report.get('source_unchanged') or not report.get('completed_at')):
        raise ValueError('验证未通过或缺少源码绑定证据；请重新执行')
    config = load_config(root)
    profile = report.get('profile')
    if profile not in config['profiles']:
        raise ValueError('验证报告缺少有效 profile')
    current = source_snapshot(root, config, profile)
    if report.get('source_before') != current or report.get('source_after') != current:
        raise ValueError('验证后输入已变化，旧结果不能用于当前内容')
    if staged and source_snapshot(root, config, profile, staged=True) != current:
        raise ValueError('暂存内容与已测试工作区不一致')
    print('验证结果与当前输入' + ('及暂存区' if staged else '') + '一致：' + str(result))
    return report


def run(root, profile):
    root = root.resolve()
    config = load_config(root)
    if profile not in config['profiles']:
        raise ValueError('未配置所选 profile：' + profile)
    source_before = source_snapshot(root, config, profile)
    evidence = local_path(root, 'logs/project-checks')
    evidence.mkdir(parents=True, exist_ok=True)
    run_dir = evidence / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    run_dir.mkdir()
    head = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    report = {'schema_version': 1, 'profile': profile,
              'started_at': datetime.now(timezone.utc).isoformat(),
              'head': head.stdout.strip() if head.returncode == 0 else None,
              'scope': 'working-tree', 'source_before': source_before,
              'results': [], 'status': '未验证'}
    for name in config['profiles'][profile]:
        check = config['checks'][name]
        started = time.monotonic()
        item = {'name': name, 'argv': check['argv'], 'cwd': check.get('cwd', '.'),
                'log': name + '.log', 'status': '未验证', 'exit_code': None}
        with (run_dir / item['log']).open('wb') as stream:
            try:
                process = subprocess.Popen(check['argv'], cwd=local_path(root, item['cwd']),
                                           stdin=subprocess.DEVNULL, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    item['exit_code'] = process.wait(timeout=check.get('timeout_seconds', 900))
                    item['status'] = '通过' if item['exit_code'] == 0 else '失败'
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    item['status'] = '超时'
            except OSError as error:
                item.update(status='无法执行', error=str(error))
        item['duration_seconds'] = round(time.monotonic() - started, 3)
        report['results'].append(item)
        print(name + '：' + item['status'])
        (run_dir / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    report['status'] = '通过' if all(item['status'] == '通过' for item in report['results']) else '失败'
    try:
        report['source_after'] = source_snapshot(root, load_config(root), profile)
        report['source_unchanged'] = report['source_after'] == source_before
    except (OSError, ValueError) as error:
        report['source_unchanged'] = False
        report['source_error'] = str(error)
    if not report['source_unchanged']:
        report['status'] = '输入已变化，需重测'
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    target = run_dir / 'result.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('验证证据：' + str(target))
    return target, report['status'] == '通过'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('.'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    verifier = sub.add_parser('verify')
    verifier.add_argument('--result', required=True)
    verifier.add_argument('--staged', action='store_true')
    runner = sub.add_parser('run')
    runner.add_argument('--profile', required=True)
    args = parser.parse_args()
    try:
        root = args.project.resolve()
        if args.command == 'list':
            print(json.dumps(load_config(root), ensure_ascii=False, indent=2))
        elif args.command == 'verify':
            verify(root, args.result, args.staged)
        else:
            return 0 if run(root, args.profile)[1] else 1
    except (ValueError, OSError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(2, str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
