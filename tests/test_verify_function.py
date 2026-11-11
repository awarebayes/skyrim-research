"""Tests for tools/verifier/verify_function.py using only original synthetic fixtures."""
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import synthetic_pecoff as sp  # noqa: E402
import verify_function as vf  # noqa: E402

LONG_HEX = re.compile(r'[0-9a-fA-F]{16,}')


class VerifyFunctionTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())
        # The comparator only writes diagnostics under the checkout's private root.
        vf.PRIVATE_ROOT.mkdir(exist_ok=True)
        self.private = Path(tempfile.mkdtemp(dir=vf.PRIVATE_ROOT, prefix='test-verify-'))

    def tearDown(self):
        shutil.rmtree(self.work)
        shutil.rmtree(self.private)

    def write_inputs(self, obj=None, image=None, task_overrides=None, record_overrides=None):
        inputs = sp.inputs(obj=obj, image=image)
        task = dict(inputs['task'], **(task_overrides or {}))
        record = dict(inputs['build_record'], **(record_overrides or {}))
        paths = {}
        for name, blob in (('candidate.coff', inputs['object_bytes']), ('image.pe', inputs['image_bytes']),
                           ('recipe.json', inputs['recipe_bytes'])):
            paths[name] = self.work / name
            paths[name].write_bytes(blob)
        for name, value in (('manifest.json', inputs['manifest']), ('symbols.json', inputs['symbol_map']),
                            ('build-record.json', record)):
            paths[name] = self.work / name
            paths[name].write_text(json.dumps(value))
        paths['task-file'] = self.work / 'task-file.json'
        paths['task-file'].write_text(json.dumps({'verify_task_schema': 1, 'task': task, 'recipe': 'recipe.json',
                                                  'symbols': 'symbols.json', 'manifest': 'manifest.json'}))
        return paths

    def verify(self, paths, image=None, obj=None, diagnostics=None):
        report = self.work / 'out' / 'report.json'
        status, text = vf.run(paths['task-file'], obj or paths['candidate.coff'], paths['build-record.json'],
                              image or paths['image.pe'], report,
                              diagnostics or self.private / 'diagnostics.json')
        return status, text, json.loads(report.read_text())

    def assert_no_bytes(self, text):
        for run in LONG_HEX.findall(text):
            self.fail(f'summary carries a long hex run: {run[:8]}...')

    def test_synthetic_pass_is_not_acceptance(self):
        status, text, report = self.verify(self.write_inputs())
        self.assertEqual(status, 0)
        self.assertEqual((report['result'], report['reason']), ('pass', 'all-checks-passed'))
        self.assertEqual(report['acceptance'], 'not-evaluated')
        self.assertIn('PASS', text)
        self.assertIn('not-evaluated', text)
        self.assertNotIn('matched', text.replace('nothing becomes matched', ''))
        self.assert_no_bytes(text)

    def test_code_mismatch_summary_has_no_bytes(self):
        image = sp.pe_image(patch={0x05: 0x90})
        paths = self.write_inputs(image=image)
        status, text, report = self.verify(paths)
        self.assertEqual(status, 1)
        self.assertEqual(report['reason'], 'code-byte-mismatch')
        diagnostics = json.loads((self.private / 'diagnostics.json').read_text())
        self.assertTrue(diagnostics['raw'])
        for value in diagnostics['raw'].values():
            if isinstance(value, str):
                self.assertNotIn(value, text)
        self.assert_no_bytes(text)
        self.assertIn(str(self.private / 'diagnostics.json'), text)

    def test_wrong_image_rejected(self):
        paths = self.write_inputs()
        other = self.work / 'other.pe'
        other.write_bytes(sp.pe_image(link_addresses={sp.CALLEE: sp.LAYOUT[sp.OTHER_CALLEE]}))
        status, _, report = self.verify(paths, image=other)
        self.assertEqual((status, report['reason']), (1, 'image-hash-mismatch'))

    def test_short_candidate_rejected(self):
        paths = self.write_inputs(obj=sp.coff_object(code=sp.CODE[:-1]))
        status, _, report = self.verify(paths)
        self.assertEqual((status, report['reason']), (1, 'function-size-mismatch'))

    def test_task_range_over_claim_rejected(self):
        paths = self.write_inputs(task_overrides={'size': len(sp.CODE) + 4})
        status, _, report = self.verify(paths)
        self.assertEqual((status, report['reason']), (1, 'function-size-mismatch'))

    def test_unreadable_input_writes_error_record(self):
        paths = self.write_inputs()
        status, text, report = self.verify(paths, obj=self.work / 'missing.coff')
        self.assertEqual(status, 2)
        self.assertEqual(report['result'], 'error')
        self.assertEqual(report['acceptance'], 'not-evaluated')
        self.assertIn('ERROR', text)

    def test_diagnostics_must_stay_private(self):
        paths = self.write_inputs()
        with self.assertRaisesRegex(vf.TaskFileError, 'diagnostics'):
            self.verify(paths, diagnostics=self.work / 'diagnostics.json')

    def test_task_file_schema_required(self):
        paths = self.write_inputs()
        spec = json.loads(paths['task-file'].read_text())
        spec['verify_task_schema'] = 2
        paths['task-file'].write_text(json.dumps(spec))
        with self.assertRaisesRegex(vf.TaskFileError, 'schema'):
            self.verify(paths)

    def test_report_check_refuses_unsanitized_or_accepting_reports(self):
        good = {'acceptance': 'not-evaluated', 'result': 'fail', 'reason': 'code-byte-mismatch', 'detail': 'x'}
        vf.check_report(dict(good))
        for bad in (dict(good, acceptance='accepted'), dict(good, result='matched'),
                    dict(good, result='pass'), dict(good, detail='bytes 4883ec288b09e800')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                vf.check_report(bad)


if __name__ == '__main__':
    unittest.main()
