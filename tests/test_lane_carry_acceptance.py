"""Idempotent lane carry on real comparator output from original synthetic fixtures."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import accept_function as af
import check
import family_review as fr
import flow
import flow_lane
import lane_accept
import test_acceptance_batch as batches
import test_acceptance_flow as acceptance


class CarryAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.case = batches.AcceptanceBatchTests('runTest')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root, self.fx = self.case.root, self.case.fx
        self.before = datetime(2000, 1, 3, tzinfo=timezone.utc)
        self.when = datetime(2000, 1, 4, tzinfo=timezone.utc)

    def test_identical_local_approval_is_carried_without_rewriting_its_record(self):
        requests = self.case.requests(self.fx.later[:2])
        af.accept_reviews(self.root, requests, self.before)
        data, _ = af.load(self.root)
        rows = copy.deepcopy(data['functions'])
        reviews = {p: p.read_bytes() for p in (self.root / 'reports').rglob('*.review.json')}
        with patch.object(af, 'validate_match', wraps=af.validate_match) as matches, \
                patch.object(af, 'validate_review', wraps=af.validate_review) as approvals:
            result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(result['accepted'], requests)
        self.assertGreaterEqual(matches.call_count, len(requests))
        self.assertGreaterEqual(approvals.call_count, len(requests))
        self.assertEqual(af.load(self.root)[0]['functions'], rows)
        self.assertEqual({p: p.read_bytes() for p in reviews}, reviews)
        # The ordinary acceptance command retains its existing refusal; carry is lane-only.
        with self.assertRaisesRegex(af.Refused, 'already matched'):
            af.accept_reviews(self.root, requests, self.when)

    def test_mixed_local_and_new_acceptances_equal_the_two_stage_public_bytes(self):
        requests = self.case.requests(self.fx.later[:3])
        af.accept_reviews(self.root, requests[:1], self.before)
        local = self.case.public()
        af.accept_reviews(self.root, requests[1:], self.when)
        expected = self.case.public()
        self.case.restore(local)
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(self.case.public(), expected)

    def test_carry_preserves_noncanonical_but_valid_review_record_bytes(self):
        requests = self.case.requests(self.fx.later[:1])
        af.accept_reviews(self.root, requests, self.before)
        fn = next(f for f in af.load(self.root)[0]['functions'] if f['id'] == self.fx.later[0])
        path = self.root / af.review_record_path(fn)
        path.write_text(json.dumps(json.loads(path.read_text()), indent=4) + '\n')
        before = path.read_bytes()
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(path.read_bytes(), before)

    def test_other_review_on_the_same_digest_does_not_become_a_carry(self):
        requests = self.case.requests(self.fx.later[:1])
        af.accept_reviews(self.root, requests, self.before)
        path = Path(requests[0]['review'])
        path.write_text(path.read_text() + '\n')
        before = self.case.public()
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['accepted'])
        self.assertIn('already matched', result['dropped'][0]['reason'])
        self.assertEqual(self.case.public(), before)

    def test_sanitized_record_must_agree_with_private_review_findings(self):
        requests = self.case.requests(self.fx.later[:1])
        af.accept_reviews(self.root, requests, self.before)
        fn = next(f for f in af.load(self.root)[0]['functions'] if f['id'] == self.fx.later[0])
        path = self.root / af.review_record_path(fn)
        record = fr.read(self.root, af.review_record_path(fn))
        record['naming_findings'] = ['Synthetic name remains uncertain.']
        path.write_text(json.dumps(record))
        before = self.case.public()
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['accepted'])
        self.assertEqual(self.case.public(), before)

    def test_same_approval_cannot_bypass_two_independent_hosts(self):
        requests = self.case.requests(self.fx.later[:1])
        af.accept_reviews(self.root, requests, self.before)
        fn = next(f for f in af.load(self.root)[0]['functions'] if f['id'] == self.fx.later[0])
        record = fr.read(self.root, fn['report'])
        record['runs'][1]['compiled_on'] = record['runs'][0]['compiled_on']
        record['runs'][1]['compared_on'] = record['runs'][0]['compared_on']
        fr.write(self.root, fn['report'], record)
        before = self.case.public()
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['dropped'])
        self.assertEqual(self.case.public(), before)

    def test_locally_accepted_samples_and_bulk_equal_sequential_acceptance(self):
        self.fx.ready()
        sample = dict(kind='review', review=str(self.root / '.local/reviews/sample.md'),
                      functions=self.fx.batch['sample'], profile='cheap')
        family = dict(kind='family', path=self.fx.batch_path, functions=self.fx.unsampled, profile='cheap')
        local = self.case.public()
        af.accept_family_batch(self.root, self.fx.batch_path, self.when, 'cheap', self.fx.fdir)
        expected = self.case.public()
        self.case.restore(local)
        with patch.object(af, 'write_progress', wraps=af.write_progress) as progress:
            result = lane_accept.accept(self.root, [family, sample], self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(progress.call_count, 1)
        self.assertEqual(self.case.public(), expected)

    def test_missing_second_sample_review_still_holds_bulk_and_changes_nothing(self):
        self.fx.ready()
        (self.root / '.local/reviews/sample-s.md').unlink()
        requests = [dict(kind='review', review=str(self.root / '.local/reviews/sample.md'),
                         functions=self.fx.batch['sample'], profile='cheap'),
                    dict(kind='family', path=self.fx.batch_path, functions=self.fx.unsampled, profile='cheap')]
        before = self.case.public()
        result = lane_accept.accept(self.root, requests, self.when)
        self.assertTrue(any(r['request']['kind'] == 'family' for r in result['dropped']))
        self.assertEqual(self.case.public(), before)

    def delta_fixture(self):
        case = acceptance.DeltaReviewTests('runTest')
        case.setUp()
        self.addCleanup(case.doCleanups)
        self.addCleanup(case.tearDown)
        return case

    def test_identical_completed_delta_keeps_its_original_approval_chain(self):
        case = self.delta_fixture()
        case.accept_full()
        old = case.grow_unit()
        case.delta(old)
        path = case.root / acceptance.REVIEW
        original = path.read_bytes()
        request = dict(kind='review', review=str(case.root / '.local/reviews/review-delta.md'),
                       functions=[case.fn['id']], profile='cheap')
        result = lane_accept.accept(case.root, [request], self.when)
        self.assertFalse(result['dropped'])
        self.assertEqual(path.read_bytes(), original)
        case.validate()

    def test_reconfirmed_changed_source_still_uses_ordinary_full_acceptance(self):
        case = self.delta_fixture()
        case.accept_full()
        case.grow_unit()
        review = case.review_file('review-new-source', [case.block()])
        request = dict(kind='review', review=str(review), functions=[case.fn['id']], profile='cheap')
        result = lane_accept.accept(case.root, [request], self.when)
        self.assertFalse(result['dropped'])
        record = json.loads((case.root / acceptance.REVIEW).read_text())
        self.assertEqual(record['review_task_id'], 'review-new-source')
        self.assertEqual(record['source_digest'], case.record['source']['digest'])
        case.validate()

    def test_real_lane_recarry_retains_locally_accepted_sample_records(self):
        remote = self.root / '.local/origin.git'
        self.fx.git('init', '--quiet', '--bare', str(remote))
        self.fx.git('remote', 'add', 'origin', str(remote))
        self.fx.git('push', '--quiet', 'origin', 'main')
        original = self.fx.git('rev-parse', 'HEAD')
        self.fx.approve_members(self.fx.batch['sample'], 'sample')
        local = self.case.public()
        af.accept_family_batch(self.root, self.fx.batch_path, self.when, 'cheap', self.fx.fdir)
        expected = self.case.public()
        self.case.restore(local)
        self.fx.reload_data()
        # Valid fresh review and sampling records, but a different review of an already accepted
        # unrelated member. It must still be refused and force the real lane re-carry path.
        with self.assertRaisesRegex(af.Refused, 'already matched'):
            self.fx.approve_members(self.fx.first[:1], 'unrelated')
        items = [flow_lane.enqueue(self.root, self.fx.fdir, 'review', [name])
                 for name in ('sample', 'unrelated')]
        items.append(flow_lane.enqueue(self.root, self.fx.fdir, 'family', [self.fx.batch_path]))
        receipt = dict(id='synthetic-carry', root=str(self.root), branch='main', items=items,
                       tooling=[], state='running', integrated=None)
        real_run = flow.run
        def run(cmd, tree, step, env=None):
            if step in ('build_progress_svg.py', 'build_model_trend.py'):
                paths = ('docs/progress.svg', 'docs/progress-map.svg') if step == 'build_progress_svg.py' else (
                    'README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg')
                for name in paths:
                    path = tree / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('Original synthetic generated output\n')
                return ''
            if step == 'check.py --staged':
                check.validate(fr.read(tree, af.PROGRESS), self.fx.target, tree)
                return 'PASS'
            return real_run(cmd, tree, step, env=env)
        def accept(tree, requests, python):
            return lane_accept.accept(tree, requests, self.when)
        with patch.object(flow_lane.resource_admission, 'admit'), \
                patch.object(flow, 'run', side_effect=run), \
                patch.object(flow_lane, 'accept', side_effect=accept) as accept_calls:
            flow_lane.build(self.root, self.fx.fdir, receipt, sys.executable, 'main')
        self.assertEqual(accept_calls.call_count, 2, repr(receipt.get('dropped')))
        self.assertEqual(len(receipt['dropped']), 1)
        self.assertEqual(receipt['dropped'][0]['request']['group'], 'unrelated')
        tree = Path(receipt['tree'])
        names = [af.PROGRESS, af.INDEX] + [n for n in expected if n.endswith('.review.json')]
        self.assertEqual({n: (tree / n).read_bytes() for n in names}, {n: expected[n] for n in names})
        self.assertEqual(self.fx.git('--git-dir', str(remote), 'rev-parse', 'main'), original)
