"""The lane batches workers, frees scheduling, retains candidates and checks every pushed tree."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_flow_multi import MultiGroupIntegration as _MultiGroupIntegration
from test_flow import git, flow
import flow_lane as lane


def stub_accept(tree, requests, python):
    # Only the acceptance implementation is stubbed in this Git/queue integration fixture.
    request_file = tree / '.local/stub-reviews.json'
    request_file.write_text(json.dumps(requests))
    flow.run([python, 'tools/accept_function.py', '--review-batch', str(request_file)], tree, 'synthetic acceptance')
    return dict(accepted=requests, dropped=[], changed=['data/progress.json', 'reconstruction/INDEX.md'] +
                [f'reports/synthetic-build/{rva}.review.json' for request in requests for rva in request['functions']])


_setup_reference = _MultiGroupIntegration.setUp
_integrate_reference = _MultiGroupIntegration.integrate
del _MultiGroupIntegration


class PushLane(unittest.TestCase):
    # Reuse the synthetic fixture; the old integration remains the equality reference.
    def setUp(self):
        _setup_reference(self)
        # These tiny queue fixtures do not depend on the host volume's free space.
        # The disk-preflight tests below exercise the real threshold separately.
        self.disk_patch = patch.object(lane.shutil, 'disk_usage',
                                       return_value=SimpleNamespace(free=10_000_000_000))
        self.disk_patch.start()
        self.addCleanup(self.disk_patch.stop)
        self.accept_patch = patch.object(lane, 'accept', side_effect=stub_accept)
        self.accept_patch.start()
        self.addCleanup(self.accept_patch.stop)

    def integrate(self, **kwargs):
        return _integrate_reference(self, **kwargs)

    def enqueue(self, names=None):
        return [lane.enqueue(self.root, self.fdir, 'review', [n]) for n in (names or self.names)]

    def lane(self, **kwargs):
        return lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0, **kwargs)

    def test_queue_combines_and_checks_once_and_retains_candidate(self):
        self.enqueue()
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = self.lane()
        self.assertEqual(checks.call_count, 1)
        self.assertEqual(result['integrated']['accepted'], 3)
        self.assertEqual(result['state'], 'done')
        self.assertTrue(Path(result['tree']).exists())
        self.assertTrue(all(i['state'] == 'done' for i in result['items']))
        self.assertEqual(git(self.root, 'rev-parse', 'origin/main'), result['integrated']['commit'])
        actions = flow.next_actions(self.root, self.fdir, online=False)
        self.assertTrue(any('flow.py sync' in text for _, text in actions))
        self.assertEqual(self.lane()['state'], 'empty')

    def test_two_input_roots_share_one_commit_and_one_check(self):
        import shutil
        other = self.tmp / 'worker-two'
        git(self.root, 'clone', '--quiet', '--branch', 'main', str(self.repo.origin), str(other))
        shutil.copytree(self.root / '.local/reviews', other / '.local/reviews')
        lane.enqueue(self.root, self.fdir, 'review', [self.names[0]])
        lane.enqueue(other, self.fdir, 'review', [self.names[1]])
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = self.lane()
        self.assertEqual(checks.call_count, 1)
        self.assertEqual(result['integrated']['accepted'], 3)
        self.assertEqual({i['root'] for i in result['items']}, {str(self.root), str(other)})

    def test_changed_sampling_state_after_checks_never_pushes(self):
        self.enqueue()
        before = git(self.repo.origin, 'rev-parse', 'main')
        original = flow.pre_push_checks
        def change(root, commit, python, **kwargs):
            original(root, commit, python, **kwargs)
            group = flow.load_group(self.fdir, self.names[0])
            group['rerun']['not_agree'] = list(group['sampled'])
            flow.save_group(self.fdir, group)
        with patch.object(flow, 'pre_push_checks', side_effect=change):
            with self.assertRaisesRegex(flow.FlowError, 'gate state changed'):
                self.lane()
        self.assertEqual(before, git(self.repo.origin, 'rev-parse', 'main'))

    def test_public_frontends_enqueue_without_running_checks(self):
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('must only enqueue')):
            self.assertEqual(flow.integrate(self.root, self.fdir, self.names[0])['state'], 'queued')
            result = flow.integrate_groups(self.root, self.fdir, self.names, 'ready-groups')
            self.assertEqual(result['selection'], self.names)
            result = flow.integrate_family(self.root, self.fdir, 'not-read-until-lane.json')
            self.assertEqual(result['state'], 'queued')

    def test_failed_member_is_not_carried_into_combined_commit(self):
        self.enqueue()
        bad = flow.load_group(self.fdir, self.names[0])['functions'][0]
        def drop(tree, requests, python):
            good = [dict(r, functions=[v for v in r['functions'] if v != bad]) for r in requests]
            good = [r for r in good if r['functions']]
            if any(bad in r['functions'] for r in requests):
                return dict(accepted=good, changed=[], dropped=[dict(function=bad, reason='synthetic gate refusal')])
            return stub_accept(tree, requests, python)
        with patch.object(lane, 'accept', side_effect=drop):
            result = self.lane()
        self.assertEqual(result['integrated']['accepted'], 2)
        data = json.loads(git(Path(result['tree']), 'show', 'HEAD:data/progress.json'))
        self.assertEqual(next(fn for fn in data['functions'] if hex(fn['rva']) == bad)['status'], 'mapped')
        self.assertEqual(len(result['dropped']), 1)

    def test_missing_member_of_multi_group_item_does_not_drop_other_group(self):
        lane.enqueue(self.root, self.fdir, 'groups', self.names, name='synthetic-multi')
        group = flow.load_group(self.fdir, self.names[-1])
        flow.review_path(self.root, group).unlink()
        result = self.lane()
        self.assertEqual(result['state'], 'done')
        self.assertEqual(len(result['accepted']), 1)
        self.assertEqual(len(result['dropped']), 1)

    def test_enqueue_idempotent_and_inflight_enqueue_is_next_run(self):
        first = self.enqueue(self.names[:1])[0]
        self.assertEqual(first, self.enqueue(self.names[:1])[0])
        original = flow.pre_push_checks
        def during(root, commit, python, **kwargs):
            self.enqueue(self.names[1:])
            original(root, commit, python, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=during):
            result = self.lane()
        self.assertEqual(len(result['items']), 1)
        queued = json.loads((self.fdir / 'lane/queue' / (self.enqueue(self.names[1:])[0]['id'] + '.json')).read_text())
        self.assertEqual(queued['state'], 'queued')

    def test_missing_group_drops_and_other_group_ships(self):
        self.enqueue()
        g = flow.load_group(self.fdir, self.names[-1])
        flow.review_path(self.root, g).unlink()
        result = self.lane()
        self.assertEqual(result['state'], 'done')
        self.assertEqual(len(result['dropped']), 1)
        expected = len(flow.load_group(self.fdir, self.names[0])['functions'])
        self.assertEqual(result['integrated']['accepted'], expected)
        data = json.loads(git(Path(result['tree']), 'show', result['integrated']['commit'] + ':data/progress.json'))
        approved = set(flow.load_group(self.fdir, self.names[0])['functions'])
        for fn in data['functions']:
            self.assertEqual(fn['status'], 'matched' if hex(fn['rva']) in approved else 'mapped')

    def test_record_rerun_during_checks_uses_real_state_lock(self):
        self.enqueue()
        original = flow.pre_push_checks
        def during(root, commit, python, **kwargs):
            group = flow.load_group(self.fdir, self.names[0])
            compare = self.tmp / 'concurrent-rerun.txt'
            compare.write_text(''.join(r + ' AGREE\n' for r in group['sampled']))
            command = [sys.executable, str(flow.TOOLS / 'flow.py'), '--root', str(self.root),
                       '--flow-dir', str(self.fdir), 'record-rerun', group['name'], '--compare', str(compare)]
            started = time.monotonic()
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(time.monotonic() - started, 10)
            original(root, commit, python, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=during):
            result = self.lane(push=False)
        self.assertIsNone(result['integrated']['pushed'])

    def test_cli_busy_lane_returns_normal_refusal_without_traceback(self):
        with lane.lane_lock(self.fdir):
            result = subprocess.run([sys.executable, str(flow.TOOLS / 'flow.py'), '--root', str(self.root),
                                     '--flow-dir', str(self.fdir), 'lane-run', '--min-free-gb', '0'],
                                    capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn('flow: push lane already running', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_next_actions_waits_for_active_lane(self):
        with lane.lane_lock(self.fdir):
            self.enqueue()
            actions = flow.next_actions(self.root, self.fdir, online=False)
        self.assertTrue(any(kind == 'wait' and 'push lane is running' in text for kind, text in actions))
        self.assertNotIn(('run', 'python3 tools/flow.py lane-run'), actions)
        self.assertIn(('run', 'python3 tools/flow.py lane-run'), flow.next_actions(self.root, self.fdir, online=False))

    def test_lane_lock_refuses_second_runner_but_not_enqueue(self):
        with lane.lane_lock(self.fdir):
            self.enqueue()
            with self.assertRaisesRegex(flow.FlowError, 'already running'):
                self.lane()

    def test_whole_tree_failure_stops_push_and_resumes_exact_candidate(self):
        self.enqueue()
        before = git(self.repo.origin, 'rev-parse', 'main')
        with patch.object(flow, 'pre_push_checks', side_effect=flow.FlowError('whole tree failed')):
            with self.assertRaisesRegex(flow.FlowError, 'whole tree failed'):
                self.lane()
        self.assertEqual(before, git(self.repo.origin, 'rev-parse', 'main'))
        receipt = lane.read(next((self.fdir / 'lane/runs').glob('*.json')))
        result = self.lane()
        self.assertEqual(receipt['integrated']['commit'], result['integrated']['commit'])

    def test_lost_race_replays_then_checks_the_exact_pushed_tree(self):
        self.enqueue()
        checked = []
        original = flow.pre_push_checks
        def during(root, commit, python, **kwargs):
            original(root, commit, python, **kwargs)
            checked.append(commit)
            if len(checked) == 1:
                other = self.tmp / 'racer'
                git(self.root, 'clone', '--quiet', '--branch', 'main', str(self.repo.origin), str(other))
                git(other, 'config', 'user.name', 'test')
                git(other, 'config', 'user.email', 'test@example.invalid')
                (other / 'extra.txt').write_text('winner\n')
                git(other, 'add', 'extra.txt')
                git(other, 'commit', '--quiet', '-m', 'race')
                git(other, 'push', '--quiet', 'origin', 'main')
        with patch.object(flow, 'pre_push_checks', side_effect=during):
            result = self.lane()
        self.assertEqual(len(checked), 2)
        self.assertEqual(checked[-1], git(self.repo.origin, 'rev-parse', 'main'))
        self.assertEqual(git(Path(result['tree']), 'show', checked[-1] + ':extra.txt'), 'winner')
        self.assertEqual(len(result['attempts']), 1)

    def test_synthetic_tree_byte_equality_with_legacy_combined_integration(self):
        fixed = datetime.datetime(2000, 1, 3, tzinfo=datetime.timezone.utc)
        real_datetime = datetime.datetime
        class Frozen(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed
        with patch.object(flow.dt, 'datetime', Frozen):
            reference = self.integrate(push=False)['integrated']['commit']
            # The copied state has legacy checkpoints; the lane never relies on them as match evidence.
            self.enqueue()
            result = self.lane(push=False)
        self.assertEqual(git(self.root, 'rev-parse', reference + '^{tree}'),
                         git(Path(result['tree']), 'rev-parse', 'HEAD^{tree}'))


from test_acceptance_flow import FlowFixture, WHEN
from test_match_gate import REVIEW
import lane_accept
import accept_function as af


class LaneAcceptance(FlowFixture, unittest.TestCase):
    def test_real_gates_and_one_index_have_byte_identical_result(self):
        review = self.review_file('review-lane', [self.block()])
        request = dict(kind='review', review=str(review), functions=[self.fn['id']])
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        af.accept_reviews(self.root, [request], WHEN)
        expected = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        for p in self.root.rglob('*'):
            if p.is_file() and p.relative_to(self.root) not in before:
                p.unlink()
        for rel, blob in before.items():
            (self.root / rel).write_bytes(blob)
        with patch.object(af, 'write_index', wraps=af.write_index) as index:
            result = lane_accept.accept(self.root, [request], WHEN)
        self.assertEqual(index.call_count, 1)
        self.assertFalse(result['dropped'])
        actual = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)

    def test_bad_member_dropped_without_applying_or_indexing(self):
        good = self.review_file('review-good', [self.block()])
        bad = self.review_file('review-bad', [self.block(digest='f' * 64)])
        requests = [dict(kind='review', review=str(bad), functions=[self.fn['id']]),
                    dict(kind='review', review=str(good), functions=[self.fn['id']])]
        with patch.object(af, 'write_index', wraps=af.write_index) as index:
            result = lane_accept.accept(self.root, requests, WHEN)
        self.assertEqual(index.call_count, 0)
        self.assertEqual(len(result['dropped']), 1)
        self.assertIn('source_digest', result['dropped'][0]['reason'])
        self.assertEqual(len(result['accepted']), 1)
        result = lane_accept.accept(self.root, result['accepted'], WHEN)
        self.assertFalse(result['dropped'])
        self.validate()

    def test_missing_second_host_cannot_enter_lane(self):
        self.record['runs'] = self.record['runs'][:1]
        self.save_record()
        review = self.review_file('review-lane', [self.block()])
        result = lane_accept.accept(self.root, [dict(kind='review', review=str(review), functions=[self.fn['id']])], WHEN)
        self.assertEqual(result['accepted'], [])
        self.assertEqual(len(result['dropped']), 1)
        self.assertFalse((self.root / REVIEW).exists())


from test_two_tier import TwoTierFixture


class LaneLabels(TwoTierFixture, unittest.TestCase):
    def test_label_only_has_identical_bytes_and_one_index(self):
        self.accept()
        self.grow_unit()
        before = self.unchanged()
        af.label_only(self.root, select={self.fn['id']}, when=WHEN)
        expected = self.unchanged()
        for rel, blob in before.items():
            if blob is not None:
                (self.root / rel).write_bytes(blob)
        with patch.object(af, 'write_index', wraps=af.write_index) as index:
            result = lane_accept.accept(self.root, [dict(kind='label', functions=[self.fn['id']])], WHEN)
        self.assertFalse(result['dropped'])
        self.assertEqual(index.call_count, 1)
        self.assertEqual(expected, self.unchanged())


class DiskPreflight(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.fdir = self.root / 'absent/flow'
        self.environment = patch.dict(os.environ, {}, clear=False)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        os.environ.pop('SKYRIM_LANE_MIN_FREE_GB', None)

    def free(self, gb):
        from types import SimpleNamespace
        return patch.object(lane.shutil, 'disk_usage', return_value=SimpleNamespace(free=gb * 1_000_000_000))

    def test_default_refuses_before_locks_or_state_mutation(self):
        with self.free(2.9), patch.object(lane, 'lane_lock') as lock:
            with self.assertRaisesRegex(flow.FlowError, r'2.90 GB free; need 3 GB'):
                lane.run_lane(self.root, self.fdir)
        lock.assert_not_called()
        self.assertFalse(self.fdir.exists())

    def test_exact_default_boundary_allows_empty_lane(self):
        with self.free(3):
            self.assertEqual(lane.run_lane(self.root, self.fdir)['state'], 'empty')

    def test_environment_and_explicit_override(self):
        with patch.dict(os.environ, {'SKYRIM_LANE_MIN_FREE_GB': '5'}), self.free(4):
            with self.assertRaisesRegex(flow.FlowError, 'need 5 GB'):
                lane.disk_preflight(self.fdir)
            lane.disk_preflight(self.fdir, min_free_gb=4)

    def test_invalid_thresholds_are_clear_refusals(self):
        for setting in ('garbage', 'nan', 'inf', '-1'):
            with self.subTest(setting=setting), patch.dict(os.environ, {'SKYRIM_LANE_MIN_FREE_GB': setting}):
                with self.assertRaisesRegex(flow.FlowError, 'finite nonnegative'):
                    lane.disk_preflight(self.fdir)

    def test_cli_override_is_wired_and_reports_failure_without_traceback(self):
        import contextlib
        import io
        error = io.StringIO()
        with patch.dict(os.environ, {'SKYRIM_LANE_MIN_FREE_GB': '1'}), self.free(3), contextlib.redirect_stderr(error):
            rc = flow.main(['--root', str(self.root), '--flow-dir', str(self.fdir), 'lane-run', '--min-free-gb', '4'])
        self.assertEqual(rc, 1)
        self.assertIn('3.00 GB free; need 4 GB', error.getvalue())
        self.assertNotIn('Traceback', error.getvalue())
        self.assertFalse(self.fdir.exists())
