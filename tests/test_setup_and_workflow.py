import importlib.util
import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.agents/skills/unity-ios-team-flow/scripts/setup_project.py'
spec = importlib.util.spec_from_file_location('unity_setup', SOURCE)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupAndWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        skill = self.root / '.agents/skills/unity-ios-team-flow'
        shutil.copytree(ROOT / '.agents/skills/unity-ios-team-flow', skill)

    def tearDown(self):
        self.temp.cleanup()

    def test_setup_preserves_existing_agents_and_does_not_replace_checks(self):
        (self.root / 'AGENTS.md').write_text('# Existing\n')
        (self.root / '.agents/project-checks.json').write_text('{"custom": true}\n')
        with contextlib.redirect_stdout(io.StringIO()):
            setup.setup(self.root, self.root / '.agents/skills/unity-ios-team-flow')
        agents = (self.root / 'AGENTS.md').read_text()
        self.assertIn('# Existing', agents)
        self.assertEqual(1, agents.count(setup.START))
        self.assertEqual({'custom': True}, json.loads((self.root / '.agents/project-checks.json').read_text()))
        self.assertTrue((self.root / 'scripts/teamflow.py').is_file())
        self.assertTrue((self.root / 'requirements').is_dir())

    def test_doctor_reads_locked_unity_version(self):
        settings = self.root / 'ProjectSettings'
        packages = self.root / 'Packages'
        settings.mkdir()
        packages.mkdir()
        (settings / 'ProjectVersion.txt').write_text('m_EditorVersion: 6000.1.12f1\n')
        (packages / 'manifest.json').write_text('{}')
        (packages / 'packages-lock.json').write_text('{}')
        self.assertEqual('6000.1.12f1', setup.unity_version(self.root))
        with contextlib.redirect_stdout(io.StringIO()):
            report = setup.diagnose(self.root)
        self.assertEqual('6000.1.12f1', report['unity_version'])

    def test_skill_routes_all_references_and_has_no_scaffold_todos(self):
        skill = ROOT / '.agents/skills/unity-ios-team-flow'
        text = (skill / 'SKILL.md').read_text()
        self.assertNotIn('[TODO', text)
        for name in ('WORKFLOW', 'UNITY-PROJECT', 'ASSETS', 'TESTING', 'PERFORMANCE',
                     'IOS-INTEGRATION', 'LOCALIZATION', 'GIT-ACTIONS', 'APP-RELEASE'):
            self.assertTrue((skill / 'references' / (name + '.md')).is_file())
        release = (skill / 'references/APP-RELEASE.md').read_text()
        self.assertIn('testFlightInternalTestingOnly', release)
        self.assertIn('Privacy Manifest', release)

    def test_upstream_sync_baseline_is_exact(self):
        upstream = (ROOT / '.agents/skills/unity-ios-team-flow/references/UPSTREAM.md').read_text()
        self.assertIn('teamflow-v3.1.2', upstream)
        self.assertIn('1217f4b7b2957bd57c649570408a9ff05045cff9', upstream)
        self.assertIn('1217f4b7b2957bd57c649570408a9ff05045cff9..目标提交', upstream)


if __name__ == '__main__':
    unittest.main()
