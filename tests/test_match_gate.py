"""The `matched` gate: a match must be tied to integrated source, pinned inputs and real reports.

Each test builds a small synthetic repository in a temporary directory. Its comparator reports
are produced by running tools/compare.py on the original synthetic fixtures, never written by
hand, so the positive case is what the real pipeline emits. Every negative case changes exactly
one thing and must be rejected for that reason.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check import validate, validate_match
from compare import compare
from source_digest import tu_digest
import synthetic_pecoff as fx

CPP = 'reconstruction/synthetic/SyntheticSum.cpp'
HDR = 'reconstruction/synthetic/SyntheticSum.h'
RECIPE = 'reconstruction/recipes/synthetic.json'
MAP = 'reports/synthetic-fixture/symbol-map.json'
RECORD = 'reports/synthetic-fixture/0x1010.json'
REVIEW = 'reports/synthetic-fixture/0x1010.review.json'
PIN = 'tools/verifier/pinned.sha256'


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


class GateFixture:
    """A synthetic repository with one function, a consistent match record and, by default, an approve."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.write(CPP, '#include "SyntheticSum.h"\nint SyntheticSum(int* p) { return SyntheticAddOne(*p); }\n')
        self.write(HDR, 'int SyntheticAddOne(int);\n')
        self.recipe_bytes = fx.recipe()
        self.write(RECIPE, self.recipe_bytes)
        compiler = json.loads(self.recipe_bytes)['compiler']['binary_sha256']
        self.write(PIN, f'{compiler}  cl.exe\n{"0" * 64}  c2.dll\n')
        self.write('findings/synthetic.md', '# synthetic\n')
        args = fx.inputs(recipe_bytes=self.recipe_bytes)
        self.image = args['image_bytes']
        symbol_map = copy.deepcopy(args['symbol_map'])
        symbol_map['symbols'][fx.FUNCTION] = {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)}
        self.write(MAP, json.dumps(symbol_map, indent=2))
        self.target = {'schema_version': 1, 'status': 'pinned', 'build_id': 'synthetic-fixture',
                       'store': 'synthetic', 'version': 'synthetic', 'architecture': 'x86-64',
                       'image_sha256': sha256(self.image)}
        self.fn = {'id': 'synthetic-fixture-0x1010', 'build_id': 'synthetic-fixture', 'rva': fx.LAYOUT[fx.FUNCTION],
                   'size': len(fx.CODE), 'status': 'matched', 'name': 'SyntheticSum', 'name_origin': 'GUESS',
                   'owner': 'test', 'evidence': 'findings/synthetic.md', 'report': RECORD}
        self.data = {'schema_version': 1, 'updated_at': '2000-01-01T00:00:00Z', 'phase': 'test',
                     'target_build_id': 'synthetic-fixture',
                     'scope': {'functions': None, 'bytes': None, 'notes': 'synthetic'},
                     'functions': [self.fn], 'work_items': [], 'milestones': []}
        self.record = self.make_record()
        self.save_record()
        self.review = self.make_review()
        self.save_review()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def run_comparator(self, obj=None, source_revision=None, source_path=CPP):
        """A report exactly as tools/compare.py writes it for the current synthetic source."""
        args = fx.inputs(obj=obj, image=self.image, recipe_bytes=self.recipe_bytes)
        revision = source_revision or tu_digest(self.root, [CPP, HDR])
        args['task'].update(source_revision=revision, source_path=source_path)
        args['build_record'].update(source_revision=revision, source_path=source_path)
        args['symbol_map'] = json.loads((self.root / MAP).read_text())
        return json.loads(json.dumps(compare(**args)))

    def make_record(self, runs=None):
        report = self.run_comparator()
        if runs is None:
            runs = [('host-a', 'host-a', report), ('host-b', 'host-b', report), ('host-a', 'host-c', report)]
        return {'match_record_schema': 1, 'function_id': self.fn['id'],
                'source': {'translation_unit': [CPP, HDR], 'compiled': CPP, 'digest_method': 'tu-sha256-v1',
                           'digest': tu_digest(self.root, [CPP, HDR])},
                'recipe': {'path': RECIPE, 'sha256': sha256(self.recipe_bytes)},
                'toolchain_pin': {'path': PIN, 'sha256': sha256((self.root / PIN).read_bytes())},
                'symbol_map': {'path': MAP, 'sha256': sha256((self.root / MAP).read_bytes())},
                'reproduction': 'synthetic', 'notes': [],
                'runs': [{'compiled_on': c, 'compared_on': h, 'report': copy.deepcopy(r)} for c, h, r in runs]}

    def save_record(self):
        self.write(RECORD, json.dumps(self.record, indent=2))

    def make_review(self):
        return {'review_record_schema': 1, 'function_id': self.fn['id'], 'build_id': self.fn['build_id'],
                'rva': self.fn['rva'], 'size': self.fn['size'], 'source_digest_method': 'tu-sha256-v1',
                'source_digest': self.record['source']['digest'], 'reviewer_model': 'claude-opus-5-5',
                'review_task_id': 'synthetic-review', 'verdict': 'approve', 'escalation_category': 'none',
                'review_sha256': 'a' * 64, 'review_date': '2000-01-02'}

    def save_review(self):
        self.write(REVIEW, json.dumps(self.review, indent=2))

    def check(self):
        return validate(self.data, self.target, root=self.root)

    def assertGateRejects(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.check()


class MatchGateTests(GateFixture, unittest.TestCase):
    # Positive case: the pipeline's own output, consistent with integrated source, passes.

    def test_consistent_record_accepted(self):
        self.assertEqual(self.record['runs'][0]['report']['result'], 'pass')
        self.check()

    def test_unmatched_entries_need_no_record(self):
        self.fn['status'] = 'reconstructed'
        del self.fn['report']
        (self.root / REVIEW).unlink()
        self.check()

    def test_mapped_entry_with_record_awaiting_review_accepted(self):
        self.fn['status'] = 'mapped'
        (self.root / REVIEW).unlink()
        self.check()

    def test_record_awaiting_review_still_checked(self):
        self.fn['status'] = 'mapped'
        (self.root / REVIEW).unlink()
        self.write(CPP, (self.root / CPP).read_text() + '// edited\n')
        self.assertGateRejects('source digest is stale')

    # A success claim without a record, or a hand-written one, is not enough.

    def test_matched_without_report_rejected(self):
        del self.fn['report']
        self.assertGateRejects('missing report path')

    def test_hand_authored_success_flag_rejected(self):
        del self.fn['report']
        self.fn['success'] = True
        self.assertGateRejects('missing report path')

    def test_hand_written_pass_report_rejected(self):
        for run in self.record['runs']:
            run['report'] = {'result': 'pass', 'reason': 'all-checks-passed'}
        self.save_record()
        self.assertGateRejects('schema or contract version')

    def test_record_outside_reports_rejected(self):
        self.write('.local/record.json', (self.root / RECORD).read_text())
        self.fn['report'] = '.local/record.json'
        self.assertGateRejects('must be under reports/')

    def test_missing_record_file_rejected(self):
        (self.root / RECORD).unlink()
        self.assertGateRejects('does not exist')

    def test_record_for_other_function_rejected(self):
        self.record['function_id'] = 'other'
        self.save_record()
        self.assertGateRejects('function_id')

    # Source: the report must be for the integrated source as it is now.

    def test_source_edited_after_report_rejected(self):
        self.write(CPP, (self.root / CPP).read_text() + '// edited\n')
        self.assertGateRejects('source digest is stale')

    def test_header_edited_after_report_rejected(self):
        self.write(HDR, 'int SyntheticAddOne(long);\n')
        self.assertGateRejects('source digest is stale')

    def test_missing_source_file_rejected(self):
        (self.root / HDR).unlink()
        self.assertGateRejects('does not exist')

    def test_source_outside_reconstruction_rejected(self):
        self.write('notes/SyntheticSum.cpp', 'x')
        self.record['source']['translation_unit'] = ['notes/SyntheticSum.cpp']
        self.record['source']['compiled'] = 'notes/SyntheticSum.cpp'
        self.save_record()
        self.assertGateRejects('must be under reconstruction/')

    def test_report_from_other_source_rejected(self):
        # Record digest updated to the new source, but the reports still describe the old one.
        self.write(CPP, (self.root / CPP).read_text() + '// edited\n')
        self.record['source']['digest'] = tu_digest(self.root, [CPP, HDR])
        self.save_record()
        self.assertGateRejects('other source than the integrated file')

    def test_report_for_other_source_path_rejected(self):
        report = self.run_comparator(source_path='reconstruction/synthetic/Other.cpp')
        self.record['runs'][1]['report'] = report
        self.save_record()
        self.assertGateRejects('other source than the integrated file')

    # Target and identity.

    def test_other_target_image_rejected(self):
        self.target['image_sha256'] = 'b' * 64
        self.assertGateRejects('not the pinned image')

    def test_inventory_range_differs_from_report_rejected(self):
        self.fn['size'] += 1
        self.assertGateRejects('function identity differs')

    def test_inventory_rva_differs_from_report_rejected(self):
        self.fn['rva'] += 0x10
        self.assertGateRejects('function identity differs')

    def test_symbol_map_not_placing_function_rejected(self):
        symbol_map = json.loads((self.root / MAP).read_text())
        symbol_map['symbols'][fx.FUNCTION]['size'] += 4
        self.write(MAP, json.dumps(symbol_map))
        self.record['symbol_map']['sha256'] = sha256((self.root / MAP).read_bytes())
        self.save_record()
        self.assertGateRejects('does not place the function')

    def test_stale_symbol_map_rejected(self):
        self.write(MAP, (self.root / MAP).read_text() + ' ')
        self.assertGateRejects('symbol map hash is stale')

    # Recipe and compiler.

    def test_recipe_changed_after_report_rejected(self):
        self.write(RECIPE, fx.recipe(flags=('/O1', '/Gy')))
        self.assertGateRejects('recipe hash is stale')

    def test_recipe_record_and_report_disagree_rejected(self):
        new = fx.recipe(flags=('/O1', '/Gy'))
        self.write(RECIPE, new)
        self.record['recipe']['sha256'] = sha256(new)
        self.save_record()
        self.assertGateRejects('report recipe differs')

    def test_compiler_not_pinned_rejected(self):
        self.write(PIN, f'{"c" * 64}  cl.exe\n')
        self.record['toolchain_pin']['sha256'] = sha256((self.root / PIN).read_bytes())
        self.save_record()
        self.assertGateRejects('not the pinned cl.exe')

    def test_stale_toolchain_pin_rejected(self):
        self.write(PIN, (self.root / PIN).read_text() + f'{"d" * 64}  link.exe\n')
        self.assertGateRejects('toolchain pin is stale')

    # Result, coverage and comparator.

    def test_failing_report_rejected(self):
        failing = self.run_comparator(obj=fx.coff_object(code=bytes([0x90]) + fx.CODE[1:]))
        self.assertEqual(failing['result'], 'fail')
        self.record['runs'][2]['report'] = failing
        self.save_record()
        self.assertGateRejects('result is not pass')

    def test_result_relabelled_as_pass_rejected(self):
        failing = self.run_comparator(obj=fx.coff_object(code=bytes([0x90]) + fx.CODE[1:]))
        failing['result'] = 'pass'
        self.record['runs'][2]['report'] = failing
        self.save_record()
        self.assertGateRejects('result is not pass')

    def test_incomplete_coverage_rejected(self):
        self.record['runs'][0]['report']['coverage']['code_bytes_exact'] -= 1
        self.save_record()
        self.assertGateRejects('coverage is incomplete')

    def test_unwind_not_checked_rejected(self):
        self.record['runs'][0]['report']['coverage']['unwind'] = 'not-checked'
        self.save_record()
        self.assertGateRejects('coverage is incomplete')

    def test_other_comparator_rejected(self):
        self.record['runs'][0]['report']['comparator']['source_sha256'] = 'e' * 64
        self.save_record()
        self.assertGateRejects('different comparator version')

    def test_edited_acceptance_rejected(self):
        self.record['runs'][0]['report']['acceptance'] = 'accepted'
        self.save_record()
        self.assertGateRejects('acceptance')

    def test_leaked_bytes_in_report_rejected(self):
        self.record['runs'][0]['report']['detail'] = 'bytes ' + '4883ec28' * 4
        self.save_record()
        self.assertGateRejects('long hex run')

    # Reproduction on more than one host.

    def test_single_run_rejected(self):
        self.record['runs'] = self.record['runs'][:1]
        self.save_record()
        self.assertGateRejects('at least 2 runs')

    def test_runs_from_one_host_rejected(self):
        for run in self.record['runs']:
            run['compiled_on'] = run['compared_on'] = 'host-a'
        self.save_record()
        self.assertGateRejects('at least 2 compile hosts')

    def test_one_compile_host_rejected(self):
        for run in self.record['runs']:
            run['compiled_on'] = 'host-a'
        self.save_record()
        self.assertGateRejects('at least 2 compile hosts')

    # Reviewer approval: a sanitized record bound to this function and this source.

    def test_missing_review_record_rejected(self):
        (self.root / REVIEW).unlink()
        self.assertGateRejects('is missing; matched needs a Reviewer approve')

    def test_review_reject_verdict_rejected(self):
        self.review.update(verdict='reject')
        self.save_review()
        self.assertGateRejects('verdict is reject, not approve')

    def test_review_escalate_verdict_rejected(self):
        self.review.update(verdict='escalate', escalation_category='provenance')
        self.save_review()
        self.assertGateRejects('verdict is escalate, not approve')

    def test_approve_with_escalation_category_rejected(self):
        self.review['escalation_category'] = 'legal'
        self.save_review()
        self.assertGateRejects('no escalation category')

    def test_review_of_other_source_digest_rejected(self):
        self.review['source_digest'] = tu_digest(self.root, [CPP])
        self.save_review()
        self.assertGateRejects('reviewed other source')

    def test_review_outlives_source_change_rejected(self):
        # Source and match record move on together; the old approval must not carry over.
        self.write(CPP, (self.root / CPP).read_text() + '// edited\n')
        self.record = self.make_record()
        self.save_record()
        self.assertGateRejects('reviewed other source')

    def test_review_for_other_function_rejected(self):
        self.review['function_id'] = 'synthetic-fixture-0x2000'
        self.save_review()
        self.assertGateRejects('reviewed another function')

    def test_review_for_other_range_rejected(self):
        self.review['size'] += 1
        self.save_review()
        self.assertGateRejects('reviewed another function')

    def test_review_at_other_function_path_not_used(self):
        (self.root / REVIEW).rename(self.root / 'reports/synthetic-fixture/0x2000.review.json')
        self.assertGateRejects('is missing')

    def test_review_without_model_rejected(self):
        self.review['reviewer_model'] = ''
        self.save_review()
        self.assertGateRejects('names no reviewer model')

    def test_review_with_free_text_rejected(self):
        self.review['reasons'] = 'prose that nobody sanitized'
        self.save_review()
        self.assertGateRejects('fields must be exactly')

    def test_review_without_hash_rejected(self):
        self.review['review_sha256'] = 'not-a-hash'
        self.save_review()
        self.assertGateRejects('review_sha256')

    def test_review_bad_date_rejected(self):
        self.review['review_date'] = '2000-02-30'
        self.save_review()
        self.assertGateRejects('review_date')

    def test_review_not_json_rejected(self):
        self.write(REVIEW, 'verdict: approve\n')
        self.assertGateRejects('is not JSON')

    def test_leftover_review_for_unmatched_entry_rejected(self):
        self.fn['status'] = 'mapped'
        self.assertGateRejects('belongs to no matched inventory entry')

    def test_validate_match_direct_call(self):
        validate_match(self.fn, self.target, self.root)


class SourceDigestTests(unittest.TestCase):
    def test_digest_covers_paths_and_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a').mkdir()
            (root / 'a/x.cpp').write_text('x')
            (root / 'a/y.h').write_text('y')
            base = tu_digest(root, ['a/y.h', 'a/x.cpp'])
            self.assertEqual(base, tu_digest(root, ['a/x.cpp', 'a/y.h']))
            self.assertNotEqual(base, tu_digest(root, ['a/x.cpp']))
            (root / 'a/z.h').write_text('y')
            self.assertNotEqual(base, tu_digest(root, ['a/x.cpp', 'a/z.h']))
            with self.assertRaisesRegex(ValueError, 'repository-relative'):
                tu_digest(root, ['../a/x.cpp'])


if __name__ == '__main__':
    unittest.main()
