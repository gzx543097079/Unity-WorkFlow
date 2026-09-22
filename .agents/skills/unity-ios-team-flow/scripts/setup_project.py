#!/usr/bin/env python3
"""把 Unity iOS TeamFlow 接入当前 Git 根；不修改 Unity 业务内容。"""
import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

START = '<!-- unity-ios-team-flow:start -->'
END = '<!-- unity-ios-team-flow:end -->'
BLOCK = '''<!-- unity-ios-team-flow:start -->
## Unity iOS 工作流

本项目使用 `.agents/skills/unity-ios-team-flow/SKILL.md`。开发变更维护一张需求卡和一份验证证据；问答、检查和只读分析不建卡。
项目空间是当前 Git 根及其目录树；处理空间外对象前先说明并取得用户本次明确允许。
不得猜测或擅自升级 Unity Editor、渲染管线、Package、Xcode 设置、签名或最低 iOS 版本；以项目锁定值为准。
有实现与交付的任务按“完成全部改动 → 环境预检 → 针对性测试 → 文件冻结 → 一次完整验证 → 目标交付”执行。
场景、Prefab、ScriptableObject、资源与 `.meta` 是一体化输入；玩家可见文本来自本地化资源。
commit、push、标签、GitHub Release，以及 Xcode 导出、Archive、TestFlight、审核、发布和下架只在用户明确目标时执行；只补齐不可缺少的前置。
普通 TestFlight 上传不启用 TestFlight Internal Only；只有明确要求仅内部测试时才设置 `testFlightInternalTestingOnly: true`。
使用 `python3 scripts/teamflow.py` 处理需求、验证和显式动作。未经明确指令不提交、不上传、不提审、不发布。
<!-- unity-ios-team-flow:end -->
'''
ENTRY = '''#!/usr/bin/env python3
"""从项目内 Skill 加载 Unity iOS TeamFlow 唯一实现。"""
import runpy
from pathlib import Path

_source = Path(__file__).resolve().parents[1] / '.agents/skills/unity-ios-team-flow/scripts/teamflow.py'
globals().update(runpy.run_path(str(_source), run_name=__name__))
'''
EMPTY_CHECKS = {'schema_version': 1, 'checks': {}, 'profiles': {},
                'inputs': ['Assets', 'Packages', 'ProjectSettings']}


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('工作流版本必须为 X.Y.Z')
    return tuple(map(int, value.split('.')))


def safe(project, name):
    path = project / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('接入路径必须位于项目内：' + name)
    for node in (path, *path.parents):
        if node == project:
            break
        if node.is_symlink():
            raise ValueError('接入路径不能含符号链接：' + name)
    return path


def agents_content(current):
    if START in current or END in current:
        if current.count(START) != 1 or current.count(END) != 1 or current.index(START) >= current.index(END):
            raise ValueError('AGENTS.md 托管标记无效')
        start, end = current.index(START), current.index(END) + len(END)
        return current[:start] + BLOCK.strip() + current[end:]
    return current + ('\n\n' if current else '') + BLOCK


def plan(project, skill):
    project, skill = project.expanduser().resolve(), skill.resolve()
    expected = project / '.agents/skills/unity-ios-team-flow'
    if skill != expected or not (skill / 'SKILL.md').is_file():
        raise ValueError('请先把完整 Skill 放到 .agents/skills/unity-ios-team-flow')
    version = (skill / 'references/VERSION').read_text().strip()
    version_tuple(version)
    manifest_path = safe(project, '.agents/teamflow.json')
    if manifest_path.exists() and json.loads(manifest_path.read_text()).get('schema_version') != 2:
        raise ValueError('检测到不兼容的旧版接入，请先人工迁移')
    agents = safe(project, 'AGENTS.md')
    planned = {
        'AGENTS.md': agents_content(agents.read_text() if agents.exists() else '').encode(),
        'scripts/teamflow.py': ENTRY.encode(),
        '.agents/teamflow.json': (json.dumps(
            {'schema_version': 2, 'skill': 'unity-ios-team-flow', 'version': version,
             'instruction_file': 'AGENTS.md'}, ensure_ascii=False, indent=2) + '\n').encode(),
    }
    checks = safe(project, '.agents/project-checks.json')
    if not checks.exists():
        planned['.agents/project-checks.json'] = (json.dumps(EMPTY_CHECKS, ensure_ascii=False, indent=2) + '\n').encode()
    return planned


def setup(project, skill, dry_run=False):
    project = project.expanduser().resolve()
    planned = plan(project, skill)
    if dry_run:
        return planned
    for name, data in planned.items():
        target = safe(project, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    safe(project, 'requirements').mkdir(exist_ok=True)
    print('项目已接入 unity-ios-team-flow：' + str(project))


def unity_version(project):
    path = project / 'ProjectSettings/ProjectVersion.txt'
    if not path.is_file():
        return None
    match = re.search(r'^m_EditorVersion:\s*(\S+)', path.read_text(), re.M)
    return match.group(1) if match else None


def diagnose(project):
    project = project.expanduser().resolve()
    items = []

    def add(name, ready, detail):
        items.append({'item': name, 'status': '就绪' if ready else '需处理', 'detail': detail})

    add('Python', sys.version_info >= (3, 9), sys.version.split()[0])
    try:
        top = subprocess.check_output(['git', '-C', str(project), 'rev-parse', '--show-toplevel'], text=True).strip()
        git_ready = Path(top).resolve() == project
    except (OSError, subprocess.CalledProcessError):
        git_ready = False
    add('Git 根目录', git_ready, '项目根必须是 Git 根')
    version = unity_version(project)
    add('Unity 项目', bool(version), 'Editor ' + version if version else '缺少 ProjectSettings/ProjectVersion.txt')
    editor = Path('/Applications/Unity/Hub/Editor') / version / 'Unity.app' if version else None
    add('Unity Editor', bool(editor and editor.is_dir()), str(editor) if editor else '无法确定精确版本')
    ios_support = editor / 'Contents/PlaybackEngines/iOSSupport' if editor else None
    add('iOS Build Support', bool(ios_support and ios_support.is_dir()), str(ios_support) if ios_support else '等待 Editor 就绪')
    add('Xcode CLI', bool(shutil.which('xcodebuild')), shutil.which('xcodebuild') or '未找到 xcodebuild')
    add('Package 锁', (project / 'Packages/manifest.json').is_file() and
        (project / 'Packages/packages-lock.json').is_file(), 'manifest.json + packages-lock.json')
    add('项目验证配置', (project / '.agents/project-checks.json').is_file(), '需填写真实无交互命令')
    report = {'project': str(project), 'unity_version': version, 'checks': items,
              'needs_action': any(item['status'] == '需处理' for item in items)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--doctor', action='store_true')
    args = parser.parse_args()
    try:
        if args.doctor:
            if args.plan:
                raise ValueError('--doctor 与 --plan 不能组合')
            diagnose(args.project)
        else:
            planned = setup(args.project, Path(__file__).resolve().parents[1], args.plan)
            if args.plan:
                print(json.dumps({name: base64.b64encode(data).decode() for name, data in planned.items()}))
            else:
                diagnose(args.project)
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
