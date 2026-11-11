"""Stale acceptances, delta reviews, batch acceptance, review packets and the generated index.

Synthetic repository from test_match_gate.GateFixture; comparator reports come from running
tools/compare.py on the synthetic fixtures, including the `candidate.code_section_sha256` the
comparator computes. Only two situations are simulated by editing that one field, because the
synthetic fixture has a single passing object: a record written before the comparator emitted it
(field removed) and an approval of other code (field replaced on the approved side, or on the
new side for a record the approval no longer describes).
"""
import contextlib
import copy
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
import build_index  # noqa: E402
from check import check_index, validate  # noqa: E402
import review_packet  # noqa: E402
from source_digest import tu_digest  # noqa: E402
from test_match_gate import CPP, HDR, RECORD, REVIEW, GateFixture  # noqa: E402

WHEN = datetime(2000, 1, 3, 4, 5, 6, tzinfo=timezone.utc)
REAL = object()  # keep the hash the comparator computed
OTHER_SECTION = 'd' * 64
OTHER = {'id': 'synthetic-fixture-0x3000', 'build_id': 'synthetic-fixture', 'rva': 0x3000, 'size': 8,
         'status': 'reconstructed', 'name': 'Other', 'name_origin': 'GUESS', 'owner': 'test',
         'evidence': 'findings/synthetic.md'}
GROWN = '\nint SyntheticTwice(int* p) { return SyntheticAddOne(*p) * 2; }\n'


def review_text(task, blocks, preamble=''):
    head = (f'{preamble}# Review {task}\n\nreviewer_model: claude-opus-5-5\nfresh_context: yes\n'
            'drafted_or_triaged_any_reviewed_function: no\ngates_in_force: G2\nsource_revision: 0000000\n'
            'sampling_second_pass: no\n')
    body = ''
    for b in blocks:
        body += (f'\n## synthetic-fixture 0x{b["rva"]:x} {b["size"]}\n\nverdict: {b.get("verdict", "approve")}\n'
                 f'escalation_category: {b.get("category", "none")}\n')
        for key in ('review_kind', 'previous_source_digest', 'code_section_unchanged'):
            if key in b:
                body += f'{key}: {b[key]}\n'
        body += f'source_paths: {CPP} {HDR}\nsource_digest: {b["digest"]}\nreport_path: {RECORD}\nreasons: synthetic\n'
    return head + body


class FlowFixture(GateFixture):
    def setUp(self):
        super().setUp()
        (self.root / REVIEW).unlink()
        self.fn['status'] = 'mapped'
        self.data['functions'].append(copy.deepcopy(OTHER))
        self.regenerate()
        self.real = self.record['runs'][0]['report']['candidate']['code_section_sha256']
        self.save_data()
        self.write('builds/target.json', json.dumps(self.target, indent=2) + '\n')

    def save_data(self):
        self.write('data/progress.json', json.dumps(self.data, indent=2) + '\n')

    def progress(self):
        return json.loads((self.root / 'data/progress.json').read_text())

    def regenerate(self, section=REAL):
        """What tools/verifier/confirm does after a unit change: fresh runs bound to the new digest.

        `section` None drops the field (a record from before the comparator emitted it); a string
        replaces it in every run (a record of other code than the synthetic object).
        """
        self.record = self.make_record()
        for run in self.record['runs']:
            candidate = run['report']['candidate']
            self.assertTrue(len(candidate['code_section_sha256']) == 64)
            if section is None:
                del candidate['code_section_sha256']
            elif section is not REAL:
                candidate['code_section_sha256'] = section
        self.save_record()

    def review_file(self, task, blocks, preamble=''):
        name = f'.local/reviews/{task}.md'
        self.write(name, review_text(task, blocks, preamble))
        return self.root / name

    def block(self, **extra):
        return dict({'rva': self.fn['rva'], 'size': self.fn['size'], 'digest': self.record['source']['digest']}, **extra)

    def accept_full(self, task='review-one'):
        changed, _ = af.accept_many(self.root, str(self.review_file(task, [self.block()])), when=WHEN)
        return changed

    def grow_unit(self, section=REAL):
        """Add a second function to the unit and re-confirm it; returns the approved digest."""
        old = self.record['source']['digest']
        self.write(CPP, (self.root / CPP).read_text() + GROWN)
        self.regenerate(section)
        return old

    def validate(self, **kw):
        return validate(self.progress(), self.target, root=self.root, **kw)


class StaleTests(FlowFixture, unittest.TestCase):
    def test_unit_change_reports_stale_by_name(self):
        self.accept_full()
        self.write(CPP, (self.root / CPP).read_text() + GROWN)
        with self.assertRaisesRegex(ValueError, r'Stale acceptance \(unit changed\).*tools/verifier/confirm') as ctx:
            self.validate()
        self.assertIn(f'[entry {self.fn["id"]}, record {RECORD}, unit {CPP}]', str(ctx.exception))

    def test_reconfirmed_record_with_old_review_reports_review_behind(self):
        self.accept_full()
        self.grow_unit()
        with self.assertRaisesRegex(ValueError, r'Stale acceptance \(review behind\).*delta review'):
            self.validate()

    def test_stale_ok_skips_but_never_accepts(self):
        self.accept_full()
        self.grow_unit()
        self.validate(stale_ok=True)
        with self.assertRaises(ValueError):
            self.validate()

    def test_index_marks_stale_and_check_index_fails_until_regenerated(self):
        self.accept_full()
        check_index(self.root, self.progress())
        self.grow_unit()
        with self.assertRaisesRegex(ValueError, 'INDEX.md is out of date'):
            check_index(self.root, self.progress())
        build_index.write_index(self.progress(), self.root)
        text = (self.root / build_index.INDEX).read_text()
        self.assertIn('matched, STALE (review behind)', text)
        self.assertIn('| `synthetic/SyntheticSum` |', text)
        self.assertIn('reconstructed |', text)

    def test_build_index_check_mode(self):
        self.accept_full()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_index.main(['--root', str(self.root), '--check']), 0)
        (self.root / build_index.INDEX).write_text('hand edited\n')
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(build_index.main(['--root', str(self.root), '--check']), 1)


class DeltaReviewTests(FlowFixture, unittest.TestCase):
    def delta(self, previous, section_flag='yes', task='review-delta'):
        block = self.block(review_kind='delta', previous_source_digest=previous, code_section_unchanged=section_flag)
        return af.accept_many(self.root, str(self.review_file(task, [block])), when=WHEN)

    def test_delta_review_clears_stale_acceptance(self):
        self.accept_full()
        first = json.loads((self.root / REVIEW).read_text())
        self.assertEqual((first['review_kind'], first['code_section_sha256']), ('full', self.real))
        old = self.grow_unit()
        changed, _ = self.delta(old)
        self.assertIn(REVIEW, changed)
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual(review['review_kind'], 'delta')
        self.assertEqual(review['previous_source_digest'], old)
        self.assertEqual(review['source_digest'], tu_digest(self.root, [CPP, HDR]))
        self.assertEqual(review['previous_review_sha256'], first['review_sha256'])
        self.assertEqual(review['previous_code_section_sha256'], self.real)
        self.assertEqual(review['code_section_sha256'], self.real)
        self.validate()
        check_index(self.root, self.progress())
        self.assertIn('| matched | delta |', (self.root / build_index.INDEX).read_text())

    def assertDeltaRefused(self, pattern, previous=None, **kw):
        before = {p: (self.root / p).read_bytes() for p in ('data/progress.json', REVIEW)}
        with self.assertRaisesRegex((af.Refused, ValueError), pattern):
            self.delta(previous or self.approved, **kw)
        self.assertEqual({p: (self.root / p).read_bytes() for p in before}, before)

    def test_delta_refused_when_code_section_changed(self):
        # The approval covered other code; the re-confirmed record is the comparator's own output.
        self.regenerate(OTHER_SECTION)
        self.accept_full()
        self.approved = self.grow_unit()
        self.assertDeltaRefused('compared code section changed')

    def test_delta_refused_when_new_record_has_no_code_section_hash(self):
        self.accept_full()
        self.approved = self.grow_unit(section=None)
        self.assertDeltaRefused('carries no code-section hash')

    def test_delta_refused_when_approved_record_had_no_code_section_hash(self):
        # Approved from a record written before the comparator emitted the hash; no git history here.
        self.regenerate(None)
        self.accept_full()
        self.approved = self.grow_unit()
        self.assertDeltaRefused('no code-section hash for the approved digest')

    def test_delta_refused_from_other_previous_digest(self):
        self.accept_full()
        self.approved = self.grow_unit()
        self.assertDeltaRefused('not the digest the superseded Reviewer record approved', previous='e' * 64)

    def test_delta_refused_without_code_section_statement(self):
        self.accept_full()
        self.approved = self.grow_unit()
        self.assertDeltaRefused('code_section_unchanged: yes', section_flag='no')

    def test_delta_refused_for_unaccepted_function(self):
        with self.assertRaisesRegex(af.Refused, 'needs one, do a full review'):
            self.delta('e' * 64)

    def test_delta_refused_while_record_is_stale(self):
        self.accept_full()
        self.approved = self.record['source']['digest']
        self.write(CPP, (self.root / CPP).read_text() + GROWN)
        with self.assertRaisesRegex(ValueError, 'source digest is stale'):
            self.delta(self.approved)

    def test_full_rereview_clears_stale_acceptance(self):
        self.regenerate(OTHER_SECTION)
        self.accept_full()
        self.grow_unit()
        af.accept_many(self.root, str(self.review_file('review-again', [self.block()])), when=WHEN)
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual((review['review_kind'], review['code_section_sha256']), ('full', self.real))
        self.validate()

    def test_current_acceptance_still_refused_as_already_matched(self):
        self.accept_full()
        with self.assertRaisesRegex(af.Refused, 'already matched'):
            self.accept_full(task='review-two')


class ReviewRecordSchemaTests(FlowFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.accept_full()
        old = self.grow_unit()
        block = self.block(review_kind='delta', previous_source_digest=old, code_section_unchanged='yes')
        af.accept_many(self.root, str(self.review_file('review-delta', [block])), when=WHEN)
        self.delta = json.loads((self.root / REVIEW).read_text())

    def rejects(self, pattern, **change):
        self.write(REVIEW, json.dumps(dict(self.delta, **change)))
        with self.assertRaisesRegex(ValueError, pattern):
            self.validate()

    def test_delta_record_accepted(self):
        self.validate()

    def test_delta_with_changed_previous_section_rejected(self):
        self.rejects('compared code section changed', previous_code_section_sha256=OTHER_SECTION)

    def test_delta_with_other_section_than_record_rejected(self):
        self.rejects('differs from the match record', code_section_sha256=OTHER_SECTION)

    def test_delta_previous_equal_to_current_rejected(self):
        self.rejects('previous_source_digest other than', previous_source_digest=self.delta['source_digest'])

    def test_delta_without_previous_review_rejected(self):
        self.rejects('previous_review_sha256', previous_review_sha256=None)

    def test_unknown_kind_rejected(self):
        self.rejects('review_kind must be', review_kind='partial')

    def test_full_with_previous_fields_rejected(self):
        self.rejects('a full review names no previous', review_kind='full')

    def test_schema_2_missing_field_rejected(self):
        review = dict(self.delta)
        del review['review_kind']
        self.write(REVIEW, json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'fields must be exactly'):
            self.validate()

    def test_schema_1_with_delta_fields_rejected(self):
        self.rejects('fields must be exactly', review_record_schema=1)

    def test_runs_disagreeing_on_code_section_rejected(self):
        self.record['runs'][1]['report']['candidate']['code_section_sha256'] = OTHER_SECTION
        self.save_record()
        with self.assertRaisesRegex(ValueError, 'runs disagree'):
            self.validate()

    def test_code_section_on_some_runs_only_rejected(self):
        del self.record['runs'][1]['report']['candidate']['code_section_sha256']
        self.save_record()
        with self.assertRaisesRegex(ValueError, 'every run or none'):
            self.validate()

    def test_code_section_must_be_a_hash(self):
        for run in self.record['runs']:
            run['report']['candidate']['code_section_sha256'] = 'C' * 64
        self.save_record()
        with self.assertRaisesRegex(ValueError, 'every run or none'):
            self.validate()


class BatchAndInputTests(FlowFixture, unittest.TestCase):
    def test_all_approved_accepts_approves_and_lists_the_rest(self):
        blocks = [self.block(), {'rva': 0x3000, 'size': 8, 'digest': 'e' * 64, 'verdict': 'reject'}]
        changed, skipped = af.accept_many(self.root, str(self.review_file('review-batch', blocks)), when=WHEN)
        self.assertEqual(changed, ['data/progress.json', REVIEW, build_index.INDEX])
        self.assertEqual(skipped, ['synthetic-fixture 0x3000 8: verdict reject'])
        self.assertEqual([f['status'] for f in self.progress()['functions']], ['matched', 'reconstructed'])
        self.assertEqual(self.progress()['updated_at'], '2000-01-03T04:05:06Z')
        self.validate()

    def test_all_approved_is_all_or_nothing(self):
        blocks = [self.block(), {'rva': 0x3000, 'size': 8, 'digest': 'e' * 64}]
        before = (self.root / 'data/progress.json').read_bytes()
        with self.assertRaisesRegex(af.Refused, 'names no match record'):
            af.accept_many(self.root, str(self.review_file('review-batch', blocks)), when=WHEN)
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), before)
        self.assertFalse((self.root / REVIEW).exists() or (self.root / build_index.INDEX).exists())

    def test_all_approved_without_approve_refused(self):
        blocks = [self.block(verdict='reject')]
        with self.assertRaisesRegex(af.Refused, 'no approve block'):
            af.accept_many(self.root, str(self.review_file('review-batch', blocks)), when=WHEN)

    def test_review_from_transcript_outside_repository_is_saved_privately(self):
        text = review_text('review-transcript', [self.block()], preamble='Here is my review.\n\n```text\n') + '```\nDone.\n'
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / 'transcript.txt'
            path.write_text(text)
            af.accept_many(self.root, str(path), when=WHEN)
        saved = self.root / '.local/reviews/review-transcript.md'
        self.assertTrue(saved.read_text().startswith('# Review review-transcript\n'))
        self.assertNotIn('```', saved.read_text())
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual(review['review_sha256'], hashlib.sha256(saved.read_bytes()).hexdigest())

    def test_review_from_stdin(self):
        stdin = sys.stdin
        sys.stdin = io.StringIO(review_text('review-stdin', [self.block()]))
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                status = af.main(['--root', str(self.root), '--all-approved', '--review', '-'])
        finally:
            sys.stdin = stdin
        self.assertEqual(status, 0)
        self.assertIn('git add -- data/progress.json', out.getvalue())
        self.assertTrue((self.root / '.local/reviews/review-stdin.md').is_file())
        self.validate()

    def test_saved_review_with_other_content_refused(self):
        self.write('.local/reviews/review-stdin.md', 'something else\n')
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / 'r.md'
            path.write_text(review_text('review-stdin', [self.block()]))
            with self.assertRaisesRegex(af.Refused, 'already exists with other content'):
                af.accept_many(self.root, str(path), when=WHEN)

    def test_review_inside_repository_outside_local_refused(self):
        self.write('notes/review.md', review_text('review-notes', [self.block()]))
        with self.assertRaisesRegex(af.Refused, 'must be under .local/reviews'):
            af.accept_many(self.root, str(self.root / 'notes/review.md'), when=WHEN)


def git(root, *args):
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false',
                    *args], cwd=root, check=True, capture_output=True)


class GitHistoryTests(FlowFixture, unittest.TestCase):
    """Schema 1 approvals carry no code-section hash; it is then taken from the record in git history."""

    def setUp(self):
        super().setUp()
        self.accept_full()
        review = json.loads((self.root / REVIEW).read_text())
        legacy = {k: v for k, v in review.items() if k not in
                  {'review_kind', 'previous_source_digest', 'previous_review_sha256',
                   'previous_code_section_sha256', 'code_section_sha256'}}
        self.write(REVIEW, json.dumps(dict(legacy, review_record_schema=1), indent=2))
        build_index.write_index(self.progress(), self.root)
        self.validate()
        git(self.root, 'init', '-q')
        git(self.root, 'add', '-A')
        git(self.root, 'commit', '-q', '-m', 'accepted')
        self.approved = self.grow_unit()

    def test_packet_shows_unit_diff_and_unchanged_code_section(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(review_packet.main(['--root', str(self.root), '--stale']), 0)
        text = out.getvalue()
        self.assertIn(f'needs: full review, or delta review with previous_source_digest: {self.approved}', text)
        self.assertIn('code section since approval: unchanged', text)
        self.assertIn('+int SyntheticTwice', text)
        self.assertIn('STALE (review behind)', text)

    def test_delta_uses_record_from_git_history(self):
        block = self.block(review_kind='delta', previous_source_digest=self.approved, code_section_unchanged='yes')
        af.accept_many(self.root, str(self.review_file('review-delta', [block])), when=WHEN)
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual((review['review_kind'], review['previous_code_section_sha256']), ('delta', self.real))
        self.validate()

    def test_delta_refused_when_history_record_had_other_section(self):
        # The committed approval holds the comparator's hash; the new record stands for other code.
        self.grow_unit(section=OTHER_SECTION)
        block = self.block(review_kind='delta', previous_source_digest=self.approved, code_section_unchanged='yes')
        with self.assertRaisesRegex(af.Refused, 'compared code section changed'):
            af.accept_many(self.root, str(self.review_file('review-delta', [block])), when=WHEN)

    def test_packet_for_current_function_needs_nothing(self):
        block = self.block(review_kind='delta', previous_source_digest=self.approved, code_section_unchanged='yes')
        af.accept_many(self.root, str(self.review_file('review-delta', [block])), when=WHEN)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            review_packet.main(['--root', str(self.root), '--no-notes', f'0x{self.fn["rva"]:x}'])
        self.assertIn('needs: nothing', out.getvalue())


if __name__ == '__main__':
    unittest.main()
