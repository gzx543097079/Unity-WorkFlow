#!/usr/bin/env python3
"""按显式清单生成可重复的 unity-work-flow ZIP，不包含项目数据。"""
import hashlib
import re
import zipfile
from pathlib import Path

SKILL = '.agents/skills/unity-work-flow'
REFERENCES = (
    'APP-RELEASE.md', 'ARCHITECTURE.md', 'ASSETS.md', 'BUGFIX.md', 'EXISTING-PROJECT.md',
    'GIT-ACTIONS.md', 'IOS-INTEGRATION.md', 'LOCALIZATION.md', 'PERFORMANCE.md',
    'PROJECT-CHECKS.md', 'RELEASE.md', 'TESTING.md', 'UNITY-PROJECT.md', 'UPSTREAM.md',
    'VERSION', 'WORKFLOW.md', 'templates/bug-fix.md', 'templates/requirement.md',
)
FILES = (
    'AGENTS.md', 'README.md', '.gitignore',
    'scripts/teamflow.py', 'scripts/package_release.py', 'scripts/validate_workflow.py',
    'tests/test_packaging.py', 'tests/test_project_checks.py',
    'tests/test_setup_and_workflow.py', 'tests/test_teamflow.py',
    SKILL + '/SKILL.md', SKILL + '/agents/openai.yaml',
    SKILL + '/scripts/project_checks.py', SKILL + '/scripts/setup_project.py',
    SKILL + '/scripts/teamflow.py',
) + tuple(SKILL + '/references/' + name for name in REFERENCES)


def version(root):
    value = (root / SKILL / 'references/VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('VERSION 必须为 X.Y.Z')
    return value


def validated_files(root, names):
    result = []
    for name in names:
        path = root / name
        if not path.is_file() or any(node.is_symlink() for node in (path, *path.parents)
                                     if node != root.parent):
            raise ValueError('分发文件缺失或包含符号链接：' + name)
        try:
            path.resolve().relative_to(root)
        except ValueError as error:
            raise ValueError('文件越出项目目录：' + name) from error
        result.append(name)
    return sorted(result)


def write_archive(root, target, entries):
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as stream:
        for source_name, archive_name in entries:
            entry = zipfile.ZipInfo(archive_name, date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            stream.writestr(entry, (root / source_name).read_bytes())
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(checksum + '  ' + target.name + '\n')
    print(target)
    return target


def package(root):
    root = root.resolve()
    names = validated_files(root, FILES)
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    target = output / ('unity-work-flow-v' + version(root) + '.zip')
    return write_archive(root, target, [(name, name) for name in names])


def package_skill(root):
    root = root.resolve()
    names = validated_files(root, [name for name in FILES if name.startswith(SKILL + '/')])
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    target = output / ('unity-work-flow-skill-v' + version(root) + '.zip')
    prefix = SKILL + '/'
    return write_archive(root, target,
                         [(name, 'unity-work-flow/' + name[len(prefix):]) for name in names])


if __name__ == '__main__':
    project = Path(__file__).resolve().parents[1]
    package(project)
    package_skill(project)
