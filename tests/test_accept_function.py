"""tools/accept_function.py on a synthetic repository: accepts only a bound approve, touches one entry."""
import copy
import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
from check import validate  # noqa: E402
from source_digest import tu_digest  # noqa: E402
from test_match_gate import CPP, HDR, RECORD, REVIEW, GateFixture  # noqa: E402

WHEN = datetime(2000, 1, 3, 4, 5, 6, tzinfo=timezone.utc)
REVIEW_FILE = '.local/reviews/synthetic-review.md'
OTHER = {'id': 'synthetic-fixture-0x3000', 'build_id': 'synthetic-fixture', 'rva': 0x3000, 'size': 8,
         'status': 'reconstructed', 'name': 'Other', 'name_origin': 'GUESS', 'owner': 'test',
         'evidence': 'findings/synthetic.md'}


class AcceptFunctionTests(GateFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        (self.root / REVIEW).unlink()
        self.fn['status'] = 'mapped'
        self.data['functions'].append(copy.deepcopy(OTHER))
        self.write('data/progress.json', json.dumps(self.data, indent=2) + '\n')
        self.write('builds/target.json', json.dumps(self.target, indent=2) + '\n')
        self.write_review()

    def write_review(self, verdict='approve', category='none', digest=None, rva=None, model='claude-opus-5-5',
                     fresh='yes', drafted='no', size=None):
        digest = digest or self.record['source']['digest']
        rva = self.fn['rva'] if rva is None else rva
        size = self.fn['size'] if size is None else size
        self.write(REVIEW_FILE, f'''# Review synthetic-review

reviewer_model: {model}
fresh_context: {fresh}
drafted_or_triaged_any_reviewed_function: {drafted}
gates_in_force: G2
source_revision: 0000000
sampling_second_pass: no

## synthetic-fixture 0x{rva:x} {size}

verdict: {verdict}
escalation_category: {category}
source_paths: {CPP} {HDR}
source_digest: {digest}
report_path: {RECORD}
reasons: synthetic
''')

    def progress(self):
        return json.loads((self.root / 'data/progress.json').read_text())

    def accept(self, verdict='approve', review=REVIEW_FILE):
        return af.accept(self.root, 'synthetic-fixture', self.fn['rva'], self.root / review, verdict, when=WHEN)

    def assertRefused(self, pattern, verdict='approve', review=REVIEW_FILE):
        before = (self.root / 'data/progress.json').read_bytes()
        with self.assertRaisesRegex((af.Refused, ValueError), pattern):
            self.accept(verdict, review)
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), before)
        self.assertFalse((self.root / REVIEW).exists())

    def test_approve_flips_only_this_entry_and_passes_the_gate(self):
        before = self.progress()
        changed = self.accept()
        self.assertEqual(changed, ['data/progress.json', REVIEW])
        after = self.progress()
        self.assertEqual(after['functions'][0]['status'], 'matched')
        self.assertEqual(after['functions'][0]['report'], RECORD)
        self.assertEqual(after['functions'][1], before['functions'][1])
        self.assertEqual(after['updated_at'], '2000-01-03T04:05:06Z')
        for key in ('work_items', 'milestones', 'scope', 'phase'):
            self.assertEqual(after[key], before[key])
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual(review['verdict'], 'approve')
        self.assertEqual(review['reviewer_model'], 'claude-opus-5-5')
        self.assertEqual(review['review_task_id'], 'synthetic-review')
        self.assertEqual(review['review_date'], '2000-01-03')
        self.assertEqual(review['source_digest'], tu_digest(self.root, [CPP, HDR]))
        self.assertEqual(review['review_sha256'], hashlib.sha256((self.root / REVIEW_FILE).read_bytes()).hexdigest())
        validate(after, self.target, root=self.root)

    def test_removing_review_record_afterwards_fails_the_gate(self):
        self.accept()
        (self.root / REVIEW).unlink()
        with self.assertRaisesRegex(ValueError, 'matched needs a Reviewer approve'):
            validate(self.progress(), self.target, root=self.root)

    def test_reject_refused(self):
        self.write_review(verdict='reject')
        self.assertRefused('only approve', verdict='reject')

    def test_escalate_refused(self):
        self.write_review(verdict='escalate', category='provenance')
        self.assertRefused('only approve', verdict='escalate')

    def test_parsed_verdict_disagrees_refused(self):
        self.write_review(verdict='reject')
        self.assertRefused("review says verdict 'reject'")

    def test_approve_with_escalation_refused(self):
        self.write_review(category='legal')
        self.assertRefused('escalation_category')

    def test_review_of_other_source_refused(self):
        self.write_review(digest='b' * 64)
        self.assertRefused('reviewed other source')

    def test_review_of_other_function_refused(self):
        self.write_review(rva=0x3000)
        self.assertRefused('0 blocks')

    def test_review_block_for_other_size_refused(self):
        self.write_review(size=self.fn['size'] + 1)
        self.assertRefused('not the inventory size')

    def test_review_block_without_size_refused(self):
        self.write_review(size='')
        self.assertRefused('gives size none')

    def assertRolledBack(self, target, error):
        before = (self.root / 'data/progress.json').read_bytes()
        original = getattr(af, target)

        calls = []

        def fail(*args, **kwargs):
            # Only fail inside the window after the review record is written, which is what is tested.
            if not (self.root / REVIEW).exists():
                return original(*args, **kwargs)
            calls.append(target)
            raise error

        setattr(af, target, fail)
        try:
            with self.assertRaises(type(error)):
                self.accept()
        finally:
            setattr(af, target, original)
        self.assertEqual(calls, [target])
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), before)
        self.assertFalse((self.root / REVIEW).exists())

    def test_unexpected_error_during_validation_rolls_back(self):
        self.assertRolledBack('validate_review', RuntimeError('synthetic crash'))

    def test_interrupt_during_validation_rolls_back(self):
        self.assertRolledBack('validate', KeyboardInterrupt())

    def test_failed_progress_write_rolls_back(self):
        self.assertRolledBack('write_progress', OSError('synthetic disk full'))

    def test_review_without_model_refused(self):
        self.write_review(model='')
        self.assertRefused('reviewer_model')

    def test_reviewer_that_drafted_refused(self):
        self.write_review(drafted='yes')
        self.assertRefused('neither drafted nor triaged')

    def test_reviewer_without_fresh_context_refused(self):
        self.write_review(fresh='no')
        self.assertRefused('fresh_context')

    def test_review_outside_private_reviews_refused(self):
        self.write('notes/review.md', (self.root / REVIEW_FILE).read_text())
        self.assertRefused('must be under .local/reviews', review='notes/review.md')

    def test_stale_match_record_refused(self):
        self.write(CPP, (self.root / CPP).read_text() + '// edited\n')
        self.assertRefused('source digest is stale')

    def test_entry_without_record_refused(self):
        data = self.progress()
        del data['functions'][0]['report']
        self.write('data/progress.json', json.dumps(data, indent=2) + '\n')
        self.assertRefused('names no match record')

    def test_unknown_entry_refused(self):
        with self.assertRaisesRegex(af.Refused, '0 inventory entries'):
            af.accept(self.root, 'synthetic-fixture', 0x4000, self.root / REVIEW_FILE, 'approve', when=WHEN)

    def test_already_matched_refused(self):
        self.accept()
        with self.assertRaisesRegex(af.Refused, 'already matched'):
            self.accept()

    def test_cli_reports_refusal(self):
        self.write_review(verdict='reject')
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            status = af.main(['--root', str(self.root), '--build-id', 'synthetic-fixture', '--rva', '0x1010',
                              '--review', str(self.root / REVIEW_FILE), '--verdict', 'reject'])
        self.assertEqual(status, 1)
        self.assertIn('REFUSED', err.getvalue())

    def test_revoke_returns_entry_to_mapped(self):
        self.accept()
        before = self.progress()
        changed, finding, note = af.revoke(self.root, 'synthetic-fixture', self.fn['rva'], 'audit found a problem',
                                           when=WHEN)
        after = self.progress()
        self.assertEqual(after['functions'][0]['status'], 'mapped')
        self.assertNotIn('report', after['functions'][0])
        self.assertEqual(after['functions'][1], before['functions'][1])
        self.assertEqual(sorted(changed), sorted(['data/progress.json', REVIEW, RECORD]))
        self.assertFalse((self.root / REVIEW).exists() or (self.root / RECORD).exists())
        self.assertEqual(finding, 'findings/synthetic.md')
        self.assertIn('2000-01-03', note)
        self.assertIn('audit found a problem', note)
        validate(after, self.target, root=self.root)

    def test_revoke_of_unaccepted_entry_refused(self):
        with self.assertRaisesRegex(af.Refused, 'not matched'):
            af.revoke(self.root, 'synthetic-fixture', self.fn['rva'], 'reason', when=WHEN)


if __name__ == '__main__':
    unittest.main()
