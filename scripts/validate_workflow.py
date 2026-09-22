#!/usr/bin/env python3
"""校验工作流仓库的入口、路由、版本和模板完整性。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/unity-ios-team-flow'


def main():
    errors = []
    required = [
        ROOT / 'AGENTS.md', ROOT / 'README.md', ROOT / '.agents/teamflow.json',
        SKILL / 'SKILL.md', SKILL / 'agents/openai.yaml', SKILL / 'references/VERSION',
        SKILL / 'references/WORKFLOW.md', SKILL / 'references/PROJECT-CHECKS.md',
        SKILL / 'references/IOS-INTEGRATION.md', SKILL / 'references/APP-RELEASE.md',
        SKILL / 'references/UPSTREAM.md', SKILL / 'references/RELEASE.md',
        SKILL / 'references/templates/requirement.md', SKILL / 'references/templates/bug-fix.md',
        SKILL / 'scripts/teamflow.py', SKILL / 'scripts/project_checks.py',
        SKILL / 'scripts/setup_project.py', ROOT / 'scripts/teamflow.py',
        ROOT / 'scripts/package_release.py', ROOT / 'tests/test_packaging.py',
    ]
    for path in required:
        if not path.is_file():
            errors.append('缺少文件：' + str(path.relative_to(ROOT)))
    if errors:
        raise SystemExit('\n'.join(errors))
    version = (SKILL / 'references/VERSION').read_text().strip()
    manifest = json.loads((ROOT / '.agents/teamflow.json').read_text())
    if manifest.get('skill') != 'unity-ios-team-flow' or manifest.get('version') != version:
        errors.append('teamflow manifest 与 Skill 版本不一致')
    if version not in (ROOT / 'README.md').read_text():
        errors.append('README 未体现当前版本：' + version)
    skill_text = (SKILL / 'SKILL.md').read_text()
    links = re.findall(r'\]\((references/[^)]+)\)', skill_text)
    for link in links:
        if not (SKILL / link).is_file():
            errors.append('Skill 路由目标不存在：' + link)
    for template in ('requirement.md', 'bug-fix.md'):
        text = (SKILL / 'references/templates' / template).read_text()
        for marker in ('<!-- teamflow:requirement:vnext -->', '- 状态：🔵 进行中',
                       '- 范围：待填写', '- 不包含：待填写', '- 验证状态：⚪ 未验证'):
            if marker not in text:
                errors.append(template + ' 缺少：' + marker)
    combined = '\n'.join((SKILL / 'references' / name).read_text()
                         for name in ('WORKFLOW.md', 'ASSETS.md', 'TESTING.md',
                                      'IOS-INTEGRATION.md', 'APP-RELEASE.md'))
    for concept in ('.meta', 'EditMode', 'PlayMode', 'IL2CPP', 'ARM64', 'Privacy Manifest',
                    'TestFlight', 'testFlightInternalTestingOnly'):
        if concept not in combined:
            errors.append('Unity/iOS 规则缺少关键概念：' + concept)
    if '[TODO' in skill_text:
        errors.append('Skill 仍含脚手架 TODO')
    upstream = (SKILL / 'references/UPSTREAM.md').read_text()
    for value in ('3.1.2', 'teamflow-v3.1.2',
                  '1217f4b7b2957bd57c649570408a9ff05045cff9'):
        if value not in upstream:
            errors.append('上游同步基线缺少：' + value)
    readme = (ROOT / 'README.md').read_text()
    for value in ('Python 3.10+', '.agents/skills/unity-ios-team-flow/', 'setup_project.py --project .',
                  'unity-ios-team-flow-skill-v' + version + '.zip', 'shasum -a 256'):
        if value not in readme:
            errors.append('README 安装说明缺少：' + value)
    if errors:
        raise SystemExit('\n'.join(errors))
    print('工作流结构、路由、版本、模板与 Unity/iOS 关键规则校验通过')


if __name__ == '__main__':
    main()
