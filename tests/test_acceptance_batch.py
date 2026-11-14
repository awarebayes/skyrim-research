"""Scoped acceptance preparation on original synthetic comparator fixtures."""
from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import accept_function as af
import lane_accept
import test_family_review as fixtures
from test_acceptance_flow import review_text


class AcceptanceBatchTests(unittest.TestCase):
    def setUp(self):
        self.fx = fixtures.FamilyReviewTests('runTest')
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.addCleanup(self.fx.tearDown)
        self.root = self.fx.root
        self.when = datetime(2000, 1, 3, tzinfo=timezone.utc)

    def requests(self, ids=None):
        ids = self.fx.later if ids is None else ids
        rows = [fn for fn in self.fx.data['functions'] if fn['id'] in ids]
        review = self.root / '.local/reviews/performance.md'
        review.write_text(review_text('performance', [dict(rva=fn['rva'], size=fn['size'],
                          digest=self.fx.records[fn['id']]['source']['digest']) for fn in rows]))
        return [dict(kind='review', review=str(review), functions=[fn['id']], profile='cheap') for fn in rows]

    def public(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*')
                if p.is_file() and not {'.git', '.local'} & set(p.relative_to(self.root).parts)}

    def restore(self, before):
        for name in self.public().keys() - before.keys():
            (self.root / name).unlink()
        for name, blob in before.items():
            (self.root / name).write_bytes(blob)

    def test_batch_bytes_equal_individual_transactions(self):
        requests = self.requests()
        before = self.public()
        for request in requests:
            af.accept_reviews(self.root, [request], self.when)
        expected = self.public()
        self.restore(before)
        with patch.object(af, 'write_progress', wraps=af.write_progress) as progress:
            result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(progress.call_count, 1)
        self.assertEqual(self.public(), expected)

    def test_fallback_keeps_decisions_and_validates_shared_snapshot_once(self):
        requests = self.requests(self.fx.first[:1] + self.fx.later[:3])
        before = self.public()
        # The uncached per-member path is the reference, including an already-matched refusal.
        expected = []
        for request in requests:
            try:
                af.accept_reviews(self.root, [request], self.when, prepare_only=True)
                expected.append(None)
            except af.Refused as error:
                expected.append(str(error))
        with patch.object(af, 'validate', wraps=af.validate) as validate, \
                patch.object(af, 'review_blocks', wraps=af.review_blocks) as parse, \
                patch.object(af, 'prepare', wraps=af.prepare) as member:
            result = lane_accept.accept(self.root, requests, self.when, prepare_only=True)
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(parse.call_count, 1)
        self.assertGreaterEqual(member.call_count, len(requests))
        self.assertEqual([d['reason'] for d in result['dropped']], [e for e in expected if e])
        self.assertEqual([r['functions'] for r in result['accepted']],
                         [r['functions'] for r, e in zip(requests, expected) if e is None])
        self.assertEqual(self.public(), before)

    def test_preparation_cost_is_one_global_scan_for_many_members(self):
        requests = self.requests()
        with patch.object(af, 'validate', wraps=af.validate) as validate, \
                patch.object(af, 'review_blocks', wraps=af.review_blocks) as parse, \
                patch.object(af, 'refuse_malformed', wraps=af.refuse_malformed) as grammar, \
                patch.object(af, 'prepare', wraps=af.prepare) as member:
            with af.acceptance_batch(self.root):
                for request in requests:
                    af.accept_reviews(self.root, [request], self.when, prepare_only=True)
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(parse.call_count, 1)
        self.assertEqual(grammar.call_count, 1)
        self.assertEqual(member.call_count, len(requests))

    def test_successful_apply_invalidates_preparation_snapshot(self):
        request = self.requests(self.fx.later[:1])[0]
        with af.acceptance_batch(self.root):
            af.accept_reviews(self.root, [request], self.when)
            with self.assertRaisesRegex(af.Refused, 'already matched'):
                af.accept_reviews(self.root, [request], self.when, prepare_only=True)

    def test_changed_review_is_not_reused(self):
        request = self.requests(self.fx.later[:1])[0]
        path = Path(request['review'])
        with af.acceptance_batch(self.root):
            af.accept_reviews(self.root, [request], self.when, prepare_only=True)
            before = path.stat()
            path.write_text(path.read_text().replace('fresh_context: yes', 'fresh_context: no '))
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            with self.assertRaisesRegex(af.Refused, 'fresh_context'):
                af.accept_reviews(self.root, [request], self.when, prepare_only=True)

    def test_inventory_and_review_hash_are_loaded_once_per_batch(self):
        requests = self.requests()
        reads = []
        read_text = Path.read_text
        def track(path, *args, **kwargs):
            reads.append(path)
            return read_text(path, *args, **kwargs)
        blob = Path(requests[0]['review']).read_bytes()
        with patch.object(Path, 'read_text', track), \
                patch.object(af.hashlib, 'sha256', wraps=af.hashlib.sha256) as sha:
            with af.acceptance_batch(self.root):
                for request in requests:
                    af.accept_reviews(self.root, [request], self.when, prepare_only=True)
        self.assertEqual(reads.count(self.root / af.PROGRESS), 1)
        self.assertEqual(reads.count(self.root / af.TARGET), 1)
        self.assertEqual(sum(bool(call.args) and call.args[0] == blob for call in sha.call_args_list), 1)

    def test_global_failure_is_preserved_without_repeating_the_scan(self):
        requests = self.requests(self.fx.later[:3])
        with patch.object(af, 'validate', side_effect=ValueError('synthetic invalid inventory')) as validate:
            with af.acceptance_batch(self.root):
                for request in requests:
                    with self.assertRaisesRegex(ValueError, 'synthetic invalid inventory'):
                        af.accept_reviews(self.root, [request], self.when, prepare_only=True)
            self.assertEqual(validate.call_count, 1)
            with self.assertRaisesRegex(ValueError, 'synthetic invalid inventory'):
                af.accept_reviews(self.root, [requests[0]], self.when, prepare_only=True)
            self.assertEqual(validate.call_count, 2)

    def test_sample_and_bulk_write_progress_once_with_identical_bytes(self):
        requests, before, public, restore = self.fx.combined_sample_inputs()
        af.accept_reviews(self.root, [requests[1]], self.when)
        af.accept_family_batch(self.root, self.fx.batch_path, self.when, 'cheap', self.fx.fdir)
        expected = public()
        restore(before)
        with patch.object(af, 'write_progress', wraps=af.write_progress) as progress:
            result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(progress.call_count, 1)
        self.assertEqual(public(), expected)


if __name__ == '__main__':
    unittest.main()
