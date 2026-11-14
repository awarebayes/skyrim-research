"""Synthetic operational ledgers only; no game inputs or machine-specific paths."""
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import pipeline_report as pr

NOW = 1800000000


class PipelineReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fdir = self.root / '.local/flow'
        self.handoffs = self.root / '.local/handoffs'
        self.handoffs.mkdir(parents=True)
        states = patch.object(pr.flow, 'function_states', return_value={})
        self.states = states.start()
        self.addCleanup(states.stop)
        for name, value in [('inventory', {'functions': []}), ('queue_units', []), ('queue_results', [])]:
            p = patch.object(pr.flow, name, return_value=value)
            p.start()
            self.addCleanup(p.stop)

    def write(self, rel, value, when=NOW - 10):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) if not isinstance(value, str) else value)
        os.utime(path, (when, when))
        return path

    def receipt(self, name='run-a', **extra):
        row = dict(id=name, state='done', owner={'pid': 42},
                   queued_at=pr.iso(NOW - 2100), lock_acquired_at=pr.iso(NOW - 2000),
                   released_at=pr.iso(NOW - 200), integrated=dict(commit='a' * 40,
                       checks=pr.iso(NOW - 1000), pushed=pr.iso(NOW - 900), ci='green',
                       wall_seconds={'checks': 800}),
                   accepted=[{'functions': ['0x1010', '0x1020']}])
        row.update(extra)
        path = self.write('.local/flow/lane/runs/' + name + '.json', row, NOW - 200)
        return path, row

    def report(self, **kw):
        return pr.report(self.root, self.fdir, self.handoffs, now=NOW, offline=True,
                         inspect_processes=False, **kw)

    def snapshot(self):
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob('*') if p.is_file()}

    def test_missing_lane_is_not_created_and_output_is_json_serializable(self):
        before = self.snapshot()
        r = self.report()
        self.assertFalse(r['queue']['busy'])
        self.assertEqual(r['summary']['hold_seconds']['n'], 0)
        self.assertIsNone(r['queue']['drain_seconds'])
        json.dumps(r)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.fdir.exists())

    def test_exact_boundaries_and_percentiles(self):
        path, row = self.receipt()
        r = self.report()
        t = r['timeline'][0]
        self.assertEqual(t['hold_seconds'], 1800)
        self.assertEqual(t['wait_seconds'], 100)
        self.assertEqual(t['ci_seconds'], 700)
        self.assertAlmostEqual(t['ci_share'], 700 / 1800)
        self.assertEqual(t['functions'], ['0x1010', '0x1020'])
        self.assertEqual(pr.distribution(range(1, 11)), dict(n=10, median=5.5, p90=9))
        self.assertEqual(t['lock_acquired']['source'], 'receipt')

    def test_mtime_estimates_are_labelled_and_no_process_birth_as_acquisition(self):
        path, row = self.receipt(lock_acquired_at=None, released_at=None)
        t = pr.timeline_row(path, row, 'lane', {})
        self.assertIn('estimate', t['lock_acquired']['source'])
        self.assertIn('mtime estimate', t['released_at']['source'])
        self.assertEqual(pr.stamp(t['checks_start']['at']), NOW - 1800)
        self.assertIsNone(pr.timeline_row(path, {'id': 'unknown', 'state': 'running'}, 'lane', {})['hold_seconds'])

    def test_per_attempt_stage_logs_and_missing_birthtime(self):
        logdir = self.root / 'logs'
        for i, name in enumerate(('check', 'tests', 'site')):
            self.write('logs/' + name + '.log', 'synthetic output', NOW - 1500 + i * 250)
        path, row = self.receipt(attempts=[dict(commit='a' * 40, logs=str(logdir))])
        before = self.snapshot()
        with patch.object(pr, 'created', return_value=None):
            t = pr.timeline_row(path, row, 'tooling', {})
        self.assertEqual(len(t['stages']), 3)
        self.assertEqual(pr.stamp(t['stages'][0]['start']['at']), NOW - 1800)
        self.assertEqual(pr.stamp(t['stages'][1]['start']['at']), NOW - 1500)
        self.assertEqual(before, self.snapshot())

    def test_busy_lock_probe_preserves_inode_and_contents(self):
        path = self.write('.local/flow/lane/.lane.lock', 'permanent inode')
        inode = path.stat().st_ino
        with path.open('rb') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertTrue(pr.lock_busy(self.fdir))
        self.assertFalse(pr.lock_busy(self.fdir))
        self.assertEqual(inode, path.stat().st_ino)
        self.assertEqual(path.read_text(), 'permanent inode')

    def test_queue_batches_acceptance_entries_together_and_tooling_separately(self):
        self.receipt()
        for n in range(3):
            self.write(f'.local/flow/lane/queue/q{n}.json', dict(id=f'q{n}', kind='review',
                       state='queued', queued_at=pr.iso(NOW - 500), owner='worker-a'))
        self.write('.local/flow/lane/tooling/t.json', dict(id='tool-a', kind='tooling',
                   state='waiting', queued_at=pr.iso(NOW - 400), owner={'pid': 55}))
        r = self.report()
        self.assertEqual(len(r['queue']['waiting']), 4)
        self.assertEqual(r['queue']['estimated_batches'], 2)
        self.assertEqual(r['queue']['drain_seconds'], 3600)
        self.assertEqual(r['queue']['waiting'][0]['owner'], 'worker-a')

    def test_funnel_uses_derived_state_and_unknown_age_without_guessing(self):
        self.states.return_value = {'0x1010': {'state': 'approved', 'group': 'g1'},
                                    '0x1020': {'state': 'drafted-pass'},
                                    '0x1030': {'state': 'rejected'},
                                    '0x1040': {'state': 'review-pending', 'group': 'g2'}}
        self.write('.local/flow/groups/g1.json', {'task_id': 'review-a'})
        self.write('.local/flow/groups/g2.json', {'created': pr.iso(NOW - 7200)})
        self.write('.local/reviews/review-a.md', 'synthetic review', NOW - 93600)
        r = self.report()['funnel']
        self.assertEqual(r['approved']['count'], 1)
        self.assertEqual(r['approved']['oldest_seconds'], 93600)
        self.assertEqual(r['approved']['buckets']['>=24h'], 1)
        self.assertEqual(r['drafted']['buckets']['unknown'], 1)
        self.assertEqual(r['review pending']['buckets']['90m-6h'], 1)
        self.assertEqual(r['rejected']['count'], 1)
        self.states.assert_called_with(self.root, self.fdir, online=True)

    def test_handoff_stall_requires_no_later_lane_progress(self):
        self.write('.local/handoffs/worker-a.md', 'Next step: resume integration\n', NOW - 10000)
        self.write('.local/handoffs/worker-b.md', '## Next step\nWait for CI\n', NOW - 100)
        r = self.report()
        self.assertTrue(r['workers'][0]['stalled'])
        self.assertFalse(r['workers'][1]['stalled'])
        self.receipt()
        self.assertFalse(self.report()['workers'][0]['stalled'])

    def test_last_next_step_ignores_fenced_code_and_redacts_paths(self):
        path = self.write('.local/handoffs/worker-a.md',
                          'Next: old\n```\nNext: code\n```\n| Next step | run /private/synthetic/input |\n')
        value = pr.last_next_step(path)
        self.assertIn('[path]', value)
        self.assertNotIn('old', value)
        self.assertNotIn('/private', value)

    def test_refusals_are_windowed_grouped_and_do_not_echo_arbitrary_logs(self):
        self.receipt(dropped=[{'reason': '0x1010: harvest differs from confirmed record'},
                             {'reason': '0x1020: harvest differs from confirmed record'}],
                     held=[{'reason': 'unfinished tooling publication; resume /private/input'}])
        self.receipt('old', error='already running')
        os.utime(self.fdir / 'lane/runs/old.json', (NOW - 90000, NOW - 90000))
        self.write('.local/flow/lane/worker.log', 'flow: push lane already running\nsecret arbitrary bytes\n')
        r = self.report()
        self.assertEqual(r['refusals']['counts']['harvest differs from confirmed record'], 2)
        self.assertEqual(r['refusals']['counts']['already running'], 1)
        self.assertEqual(r['refusals']['counts']['unfinished tooling publication'], 1)
        rendered = json.dumps(r)
        self.assertNotIn('private/input', rendered)
        self.assertNotIn('secret arbitrary', rendered)

    def test_gh_filters_exact_sha_and_preserves_per_job_timing(self):
        calls = []
        def cmd(args, root):
            calls.append(args)
            if args[2] == 'list':
                return json.dumps([dict(headSha='a' * 40, databaseId=12),
                                   dict(headSha='b' * 40, databaseId=13)])
            return json.dumps({'jobs': [dict(name='Infrastructure checks', startedAt=pr.iso(NOW - 800),
                                             completedAt=pr.iso(NOW - 300), conclusion='success')]})
        with patch.object(pr, 'command', side_effect=cmd):
            jobs = pr.github_jobs(self.root, {'a' * 40})
        self.assertEqual(len(calls), 2)
        self.assertEqual(jobs['a' * 40][0]['job'], 'Infrastructure checks')
        path, row = self.receipt()
        t = pr.timeline_row(path, row, 'lane', jobs)
        self.assertEqual(t['ci_seconds'], 500)
        self.assertEqual(t['ci_start']['source'], 'gh exact-SHA jobs')

    def test_process_waiter_age_and_flow_filter(self):
        raw = f'99 01:02:03 python tools/flow.py --flow-dir {self.fdir} tooling-push --wait-lane\n'
        raw += '100 00:50 python tools/flow.py --flow-dir elsewhere tooling-push --wait-lane\n'
        with patch.object(pr, 'command', return_value=raw):
            result = pr.process_waiters(self.root, self.fdir)
        self.assertEqual(result, [dict(id='pid:99', kind='tooling-process', owner='pid:99',
                                      age_seconds=3723, age_source='process age, upper bound on wait')])

    def test_partial_json_lines_and_invalid_receipts_are_not_repaired(self):
        self.write('.local/flow/lane/runs/inflight.json', '{')
        path = self.write('events.jsonl', '{"event":"a"}\n{')
        before = self.snapshot()
        self.assertEqual(pr.json_lines(path), [{'event': 'a'}])
        self.assertEqual(self.report()['timeline'], [])
        self.assertEqual(before, self.snapshot())

    def test_cli_writes_only_explicit_output(self):
        before = self.snapshot()
        args = ['--root', str(self.root), '--flow-dir', str(self.fdir), '--offline', '--json']
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(pr.main(args), 0)
        self.assertIn('timeline', json.loads(output.getvalue()))
        self.assertEqual(before, self.snapshot())
        target = self.root / 'report.json'
        self.assertEqual(pr.main(args + ['--output', str(target)]), 0)
        self.assertEqual(set(self.snapshot()) - set(before), {'report.json'})

    def test_late_receipt_update_uses_ci_lower_bound_instead_of_hours_of_false_hold(self):
        path, row = self.receipt()
        row.pop('released_at')
        os.utime(path, (NOW + 10000, NOW + 10000))
        jobs = {'a' * 40: [dict(start=pr.iso(NOW - 800), end=pr.iso(NOW - 300))]}
        t = pr.timeline_row(path, row, 'lane', jobs)
        self.assertEqual(t['hold_seconds'], 1700)
        self.assertIn('lower-bound estimate', t['released_at']['source'])

    def test_no_log_does_not_invent_per_stage_start_times(self):
        path, row = self.receipt()
        t = pr.timeline_row(path, row, 'lane', {})
        self.assertTrue(all(s['start']['at'] is None for s in t['stages']))

    def test_additional_log_is_read_only_and_deduplicated(self):
        path = self.write('worker.log', 'flow: push lane already running\n')
        before = self.snapshot()
        r = self.report(log_paths=[path, path])
        self.assertEqual(r['refusals']['counts']['already running'], 1)
        self.assertEqual(before, self.snapshot())

    def test_default_state_root_is_shared_checkout(self):
        with patch.object(pr, 'shared_root', return_value=self.root), \
                patch.object(pr, 'report', wraps=pr.report) as report, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pr.main(['--offline']), 0)
        self.assertEqual(report.call_args.args[:2], (self.root, self.fdir))

    def test_negative_duration_is_unknown_and_outliers_not_valid_ci_share(self):
        self.assertIsNone(pr.elapsed(20, 10))
        path, row = self.receipt()
        row['released_at'] = pr.iso(NOW - 1990)
        self.assertIsNone(pr.timeline_row(path, row, 'lane', {})['ci_share'])
        self.assertIsNone(pr.stamp('not-a-time'))
        self.assertIsNone(pr.stamp(float('nan')))


if __name__ == '__main__':
    unittest.main()
