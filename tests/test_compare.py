"""Comparator contract v1: one positive case and a rejection test for each failure it must catch."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare import ROOT, compare, sanitized
from pecoff import Reject
import synthetic_pecoff as fx


def run(**overrides):
    args = fx.inputs()
    args.update(overrides)
    return compare(**args)


class ComparatorTests(unittest.TestCase):
    def assertRejected(self, report, reason, detail=None):
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['reason'], reason, report['detail'])
        if detail:
            self.assertIn(detail, report['detail'])

    def test_fixture_link_matches_hand_computed_displacement(self):
        # call at +0x06 ends at 0x1010 + 0x0b; the callee is at 0x1000, so rel32 = -0x1b.
        image = fx.pe_image()
        text = image[0x400 + 0x10:0x400 + 0x10 + len(fx.CODE)]
        self.assertEqual(struct.unpack_from('<i', text, 7)[0], -0x1B)

    def test_positive_case_passes_with_full_coverage(self):
        report = run()
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual(cov['code_bytes_total'], len(fx.CODE))
        self.assertEqual(cov['code_bytes_exact'] + cov['code_bytes_by_reference'], len(fx.CODE))
        self.assertEqual(cov['code_bytes_by_reference'], 12)
        self.assertEqual(cov['relocations_by_type'], {'REL32': 2, 'REL32_1': 1})
        self.assertEqual((cov['unwind'], cov['unwind_entries'], cov['unwind_bytes_exact']), ('covered', 1, 8))
        self.assertEqual(report['acceptance'], 'not-evaluated')
        self.assertNotIn('matched', json.dumps(report))

    def test_report_carries_required_identity(self):
        args = fx.inputs()
        report = compare(**args)
        self.assertEqual(report['source']['source_revision'], args['task']['source_revision'])
        self.assertEqual(report['target']['image_sha256'], args['task']['target_image_sha256'])
        self.assertEqual(report['recipe']['flags'], ['/O2', '/Gy'])
        self.assertEqual(len(report['recipe']['compiler_binary_sha256']), 64)
        self.assertEqual(report['comparator']['version'], '0.1.0')
        self.assertEqual(report['function'], {'build_id': 'synthetic-fixture', 'rva': 0x1010,
                                              'size': len(fx.CODE), 'symbol': fx.FUNCTION})

    def test_changed_byte_rejected(self):
        # 0x28 -> 0x38 in `sub rsp, imm8`, a byte no relocation covers.
        report = run(**fx.inputs(image=fx.pe_image(patch={3: 0x38})))
        self.assertRejected(report, 'code-byte-mismatch', '+0x3')

    def test_wrong_call_target_rejected(self):
        image = fx.pe_image(link_addresses={fx.CALLEE: fx.LAYOUT[fx.OTHER_CALLEE]})
        report = run(**fx.inputs(image=image))
        self.assertRejected(report, 'relocation-target-mismatch', fx.CALLEE)
        self.assertIn('REL32 at +0x7', report['detail'])

    def test_wrong_data_target_rejected(self):
        image = fx.pe_image(link_addresses={fx.BASE: fx.LAYOUT[fx.BASE] + 4})
        report = run(**fx.inputs(image=image))
        self.assertRejected(report, 'relocation-target-mismatch', fx.BASE)
        self.assertIn('+0xd', report['detail'])

    def test_wrong_symbol_map_rva_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols'][fx.COUNTER]['rva'] += 8
        self.assertRejected(compare(**args), 'relocation-target-mismatch', fx.COUNTER)

    def test_unmapped_reference_rejected(self):
        args = fx.inputs()
        del args['symbol_map']['symbols'][fx.BASE]
        self.assertRejected(compare(**args), 'unresolved-symbol', fx.BASE)

    def test_truncated_function_rejected(self):
        # Candidate stops one byte early (no `ret`); the task still pins the full target range.
        obj = fx.coff_object(code=fx.CODE[:-1])
        self.assertRejected(run(**fx.inputs(obj=obj)), 'function-size-mismatch')

    def test_task_range_larger_than_candidate_rejected(self):
        args = fx.inputs()
        args['task']['size'] += 1
        self.assertRejected(compare(**args), 'function-size-mismatch')

    def test_target_range_past_raw_data_rejected(self):
        self.assertRejected(run(**fx.inputs(image=fx.pe_image(text_raw_size=0x20))), 'target-range-truncated')

    def test_truncated_object_file_rejected(self):
        obj = fx.coff_object()[:-6]
        self.assertRejected(run(**fx.inputs(obj=obj)), 'truncated-input')

    def test_wrong_image_rejected(self):
        args = fx.inputs()
        args['image_bytes'] = fx.pe_image(patch={0: 0x90})
        self.assertRejected(compare(**args), 'image-hash-mismatch')

    def test_manifest_disagreement_rejected(self):
        args = fx.inputs()
        args['manifest']['image_sha256'] = '0' * 64
        self.assertRejected(compare(**args), 'manifest-mismatch')
        args = fx.inputs()
        args['manifest']['status'] = 'unselected'
        self.assertRejected(compare(**args), 'target-unpinned')

    def test_stale_source_revision_rejected(self):
        args = fx.inputs()
        args['build_record']['source_revision'] = fx.sha256(b'older revision')[:40]
        self.assertRejected(compare(**args), 'stale-source-revision')

    def test_stale_recipe_rejected(self):
        args = fx.inputs()
        args['recipe_bytes'] = fx.recipe(flags=('/O1', '/Gy'))
        self.assertRejected(compare(**args), 'stale-recipe', 'recipe file')
        args = fx.inputs()
        args['build_record']['recipe_sha256'] = fx.sha256(b'other recipe')
        self.assertRejected(compare(**args), 'stale-recipe', 'built with a different recipe')

    def test_object_not_from_build_record_rejected(self):
        args = fx.inputs()
        args['object_bytes'] = fx.coff_object(code=fx.CODE[:3] + b'\x30' + fx.CODE[4:])
        self.assertRejected(compare(**args), 'object-provenance-mismatch')

    def test_unsupported_relocation_rejected(self):
        relocs = ((0x07, fx.CALLEE, fx.REL32), (0x0D, fx.BASE, fx.SECREL), (0x13, fx.COUNTER, fx.REL32_1))
        report = run(**fx.inputs(obj=fx.coff_object(relocs=relocs)))
        self.assertRejected(report, 'unsupported-relocation', 'SECREL')

    def test_omitted_exception_coverage_rejected(self):
        report = run(**fx.inputs(obj=fx.coff_object(unwind=False)))
        self.assertRejected(report, 'unwind-coverage-missing')

    def test_extra_candidate_unwind_rejected(self):
        report = run(**fx.inputs(image=fx.pe_image(pdata=False)))
        self.assertRejected(report, 'unwind-coverage-extra')

    def test_unwind_info_difference_rejected(self):
        # Same span, but the target records a 0x38-byte allocation.
        report = run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0104010004620000'))))
        self.assertRejected(report, 'unwind-info-mismatch')

    def test_exception_handler_fails_closed(self):
        # UNW_FLAG_EHANDLER set: handler data layout is not decoded, so the comparator must refuse.
        report = run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0904010004420000'))))
        self.assertRejected(report, 'unsupported-unwind', 'handler')

    def test_undeclared_alias_rejected_and_declared_fold_reported(self):
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticFolded'] = {'rva': fx.LAYOUT[fx.FUNCTION], 'size': None}
        self.assertRejected(compare(**args), 'undeclared-alias')
        args['symbol_map']['symbols'][fx.FUNCTION] = {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)}
        args['symbol_map']['folds'] = [[fx.FUNCTION, 'SyntheticFolded']]
        report = compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['coverage']['aliases_declared'], ['SyntheticFolded'])

    def test_overlapping_function_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticNeighbor'] = {'rva': fx.LAYOUT[fx.FUNCTION] + 0x10, 'size': 8}
        self.assertRejected(compare(**args), 'overlapping-function')
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticBefore'] = {'rva': fx.LAYOUT[fx.FUNCTION] - 4, 'size': 8}
        self.assertRejected(compare(**args), 'overlapping-function')

    def test_symbol_map_conflict_and_wrong_build_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols'][fx.FUNCTION] = {'rva': 0x1020, 'size': None}
        self.assertRejected(compare(**args), 'symbol-map-conflict')
        args = fx.inputs()
        args['symbol_map']['build_id'] = 'another-build'
        self.assertRejected(compare(**args), 'symbol-map-build-mismatch')

    def test_reports_contain_no_code_bytes(self):
        image = fx.pe_image()
        linked = image[0x400 + 0x10:0x400 + 0x10 + len(fx.CODE)]
        windows = {blob[i:i + 4].hex() for blob in (fx.CODE, linked, fx.XDATA) for i in range(len(blob) - 3)}
        reports = [run(), run(**fx.inputs(image=fx.pe_image(patch={3: 0x38}))),
                   run(**fx.inputs(image=fx.pe_image(link_addresses={fx.CALLEE: 0x1008}))),
                   run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0104010004620000'))))]
        for report in reports:
            text = json.dumps(report).lower()
            leaks = [w for w in windows if w in text]
            self.assertEqual(leaks, [], report['reason'])
            self.assertNotIn('"raw"', text)

    def test_sanitizer_refuses_hex_and_bytes(self):
        with self.assertRaisesRegex(ValueError, 'hex run'):
            sanitized({'detail': 'differs: 4883ec288b09e800'})
        with self.assertRaisesRegex(ValueError, 'raw bytes'):
            sanitized({'detail': b'\x48\x83'})
        sanitized({'image_sha256': 'a' * 64})

    def test_diagnostics_only_under_private_root(self):
        with tempfile.TemporaryDirectory() as folder:
            private = Path(folder) / 'private'
            path = private / 'compare' / 'synthetic-sum.json'
            report = run(**fx.inputs(image=fx.pe_image(patch={3: 0x38})), diagnostics=path, private_root=private)
            self.assertEqual(report['reason'], 'code-byte-mismatch')
            raw = json.loads(path.read_text())['raw']
            self.assertIn('38', raw['target'])
            with self.assertRaises(Reject) as caught:
                run(diagnostics=Path(folder) / 'public.json', private_root=private)
            self.assertEqual(caught.exception.reason, 'diagnostics-path-not-private')
            self.assertFalse((Path(folder) / 'public.json').exists())

    def test_cli_exit_codes_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for label, args in (('pass', fx.inputs()), ('fail', fx.inputs(image=fx.pe_image(patch={3: 0x38})))):
                paths = {}
                for key, name in (('task', 'task.json'), ('manifest', 'manifest.json'),
                                  ('build_record', 'build.json'), ('symbol_map', 'symbols.json')):
                    paths[key] = root / f'{label}-{name}'
                    paths[key].write_text(json.dumps(args[key]))
                for key, name in (('recipe_bytes', 'recipe.json'), ('object_bytes', 'candidate.coff'),
                                  ('image_bytes', 'target.pe')):
                    paths[key] = root / f'{label}-{name}'
                    paths[key].write_bytes(args[key])
                out = root / f'{label}-report.json'
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'tools/compare.py'), '--task', paths['task'],
                     '--manifest', paths['manifest'], '--recipe', paths['recipe_bytes'],
                     '--build-record', paths['build_record'], '--object', paths['object_bytes'],
                     '--image', paths['image_bytes'], '--symbols', paths['symbol_map'], '--report', out],
                    capture_output=True, text=True)
                report = json.loads(out.read_text())
                self.assertEqual(result.returncode, 0 if label == 'pass' else 1, result.stderr)
                self.assertEqual(report['result'], label)


if __name__ == '__main__':
    unittest.main()
