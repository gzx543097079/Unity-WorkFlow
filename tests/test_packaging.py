import hashlib
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/package_release.py'
spec = importlib.util.spec_from_file_location('unity_package_release', SOURCE)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_skill_package_has_installable_layout_and_checksum(self):
        archive = packager.package_skill(ROOT)
        copied = self.root / archive.name
        shutil.copy2(archive, copied)
        digest = hashlib.sha256(copied.read_bytes()).hexdigest()
        self.assertEqual(digest, archive.with_suffix('.zip.sha256').read_text().split()[0])
        with zipfile.ZipFile(copied) as stream:
            names = set(stream.namelist())
            self.assertIn('unity-ios-team-flow/SKILL.md', names)
            self.assertIn('unity-ios-team-flow/scripts/setup_project.py', names)
            self.assertFalse(any(name.startswith('.agents/') for name in names))

    def test_extracted_skill_can_setup_a_project(self):
        archive = packager.package_skill(ROOT)
        project = self.root / 'Game'
        skill_root = project / '.agents/skills'
        skill_root.mkdir(parents=True)
        with zipfile.ZipFile(archive) as stream:
            stream.extractall(skill_root)
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
        setup = skill_root / 'unity-ios-team-flow/scripts/setup_project.py'
        result = subprocess.run(['python3', str(setup), '--project', str(project), '--plan'],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('AGENTS.md', result.stdout)

    def test_archives_are_reproducible(self):
        first = packager.package(ROOT).read_bytes()
        second = packager.package(ROOT).read_bytes()
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
