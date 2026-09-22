import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.agents/skills/unity-work-flow/scripts/project_checks.py'
spec = importlib.util.spec_from_file_location('unity_project_checks', SOURCE)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class ProjectChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.agents').mkdir()
        (self.root / 'Assets').mkdir()
        (self.root / 'Assets/Game.cs').write_text('class Game {}\n')
        config = {
            'schema_version': 1,
            'checks': {
                'pass': {'argv': [sys.executable, '-c', 'print("ok")'], 'timeout_seconds': 30},
            },
            'profiles': {'change': ['pass']},
            'inputs': ['Assets'],
        }
        (self.root / '.agents/project-checks.json').write_text(json.dumps(config))
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'initial'], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_run_verify_and_input_change_invalidation(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result, passed = checks.run(self.root, 'change')
        self.assertTrue(passed)
        relative = str(result.resolve().relative_to(self.root.resolve()))
        self.assertEqual('通过', checks.verify(self.root, relative)['status'])
        (self.root / 'Assets/Game.cs').write_text('class Game { int Changed; }\n')
        with self.assertRaisesRegex(ValueError, '输入已变化'):
            checks.verify(self.root, relative)

    def test_generated_unity_directories_are_excluded(self):
        self.assertTrue(checks.excluded_input('Library/ArtifactDB'))
        self.assertTrue(checks.excluded_input('Temp/build.tmp'))
        self.assertTrue(checks.excluded_input('logs/editmode.xml'))
        self.assertFalse(checks.excluded_input('Assets/UI/HUD.prefab'))

    def test_rejects_shell_string_and_invalid_timeout(self):
        path = self.root / '.agents/project-checks.json'
        data = json.loads(path.read_text())
        data['checks']['pass']['argv'] = 'python3 -c pass'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'argv'):
            checks.load_config(self.root)


if __name__ == '__main__':
    unittest.main()
