import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.agents/skills/unity-work-flow/scripts/teamflow.py'
spec = importlib.util.spec_from_file_location('unity_teamflow', SOURCE)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


class TeamFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        skill = self.root / '.agents/skills/unity-work-flow'
        (skill / 'references').mkdir(parents=True)
        shutil.copytree(ROOT / '.agents/skills/unity-work-flow/references/templates',
                        skill / 'references/templates')

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, function, *args, **kwargs):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            value = function(*args, **kwargs)
        return value, stream.getvalue()

    def fill_card(self, requirement, all_done=False):
        path = self.root / 'requirements' / (requirement + '.md')
        text = path.read_text().replace('- 范围：待填写', '- 范围：战斗结算 UI')
        text = text.replace('- 不包含：待填写', '- 不包含：服务器结算逻辑')
        if all_done:
            text = text.replace('- ⚪ AC-', '- ✅ AC-')
        path.write_text(text)
        return path

    def test_create_parse_and_list_use_colored_progress(self):
        result, _ = self.capture(flow.create, self.root, '新增结算动画')
        path = self.fill_card(result['requirement'])
        card = flow.parse_card(path)
        self.assertEqual('🔵 进行中', card['state_display'])
        self.assertEqual('⚪ 0/1', card['progress']['display'])
        rows = flow.cards(self.root)
        self.assertEqual('新增结算动画', rows[0]['title'])

    def test_bug_template_and_state_reason_gate(self):
        result, _ = self.capture(flow.create, self.root, '后台恢复异常', bug=True)
        path = self.fill_card(result['requirement'])
        self.assertIn('类型：Bug 修复', path.read_text())
        with self.assertRaisesRegex(ValueError, '必须填写原因'):
            flow.set_state(self.root, result['requirement'], '阻塞')
        self.capture(flow.set_state, self.root, result['requirement'], '阻塞', '等待复现设备')
        self.assertIn('🔴 阻塞', path.read_text())

    def test_complete_requires_finished_ac_and_evidence(self):
        result, _ = self.capture(flow.create, self.root, '安全区适配')
        requirement = result['requirement']
        self.fill_card(requirement)
        with self.assertRaisesRegex(ValueError, '仍有未完成 AC'):
            flow.complete(self.root, requirement, evidence='真机录屏')
        path = self.fill_card(requirement, all_done=True)
        self.capture(flow.complete, self.root, requirement, evidence='iPhone 真机录屏')
        self.assertIn('- 状态：✅ 完成', path.read_text())
        self.assertIn('- 验证状态：✅ 通过', path.read_text())

    def test_testflight_internal_only_is_explicit(self):
        self.assertEqual({}, flow.release_options('upload-testflight'))
        self.assertEqual({'testFlightInternalTestingOnly': True},
                         flow.release_options('upload-testflight', True))
        with self.assertRaisesRegex(ValueError, '仅适用于上传 TestFlight'):
            flow.release_options('archive', True)
        _, output = self.capture(flow.release_prepare, 'export-xcode', '1.2.0', '42')
        payload = json.loads(output)
        self.assertFalse(payload['external_write'])
        self.assertEqual('导出 Xcode 工程', payload['display_name'])


if __name__ == '__main__':
    unittest.main()
