"""Tests for the queue's release, profile stamping and near-miss set-aside, the profile data,
the friction report and the review comparison. All inputs are synthetic."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
import friction  # noqa: E402
import profiles  # noqa: E402
import review_compare  # noqa: E402
import work_queue as wq  # noqa: E402
from test_flow import BUILD, review_text  # noqa: E402


def write_queue(qdir, n):
    qdir.mkdir(parents=True, exist_ok=True)
    lines = [f'.local/tasks/g/g-u{i}\treconstruction/misc/U{i}.h,reconstruction/misc/U{i}.cpp\t0x{i + 1:x}000\t3' for i in range(n)]
    (qdir / 'queue.tsv').write_text('\n'.join(lines) + '\n')


class QueueAdditions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.q = self.tmp / '.local/queue/small'
        write_queue(self.q, 2)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_release_frees_the_unit_for_another_session(self):
        u = wq.claim(self.q, 'haiku-2', t=100.0)
        with self.assertRaises(wq.QueueError):
            wq.release(self.q, u['dir'], worker='haiku-1')
        self.assertEqual(wq.release(self.q, u['dir'], worker='haiku-2', t=200.0), 'haiku-2')
        self.assertEqual(wq.claim(self.q, 'haiku-1', t=300.0)['key'], 'g-u0')
        rel = [json.loads(l) for l in (self.q / 'releases.jsonl').read_text().splitlines()]
        self.assertEqual(rel[0]['worker'], 'haiku-2')
        with self.assertRaises(wq.QueueError):
            wq.release(self.q, '.local/tasks/g/g-u1')  # not claimed

    def test_release_refuses_a_done_unit(self):
        u = wq.claim(self.q, 'haiku-2')
        wq.finish(self.q, u['dir'], [json.dumps({'unit': 'x.cpp'})])
        with self.assertRaisesRegex(wq.QueueError, 'already done'):
            wq.release(self.q, u['dir'])

    def test_results_carry_profile_and_claim_time(self):
        u = wq.claim(self.q, 'haiku-1', t=1_000_000.0, profile='cheap')
        recs = wq.finish(self.q, u['dir'], [json.dumps({'rva': '0x1000', 'result': 'pass', 'attempts': 2})], t=1_000_600.0)
        self.assertEqual(recs[0]['profile'], 'cheap')
        self.assertEqual(recs[0]['claimed'], wq.iso(1_000_000.0))
        self.assertIn('cheap', wq.stats(self.q)['profile'])

    def test_earlier_near_misses_are_set_aside_on_a_new_claim(self):
        unit = self.tmp / '.local/tasks/g/g-u0'
        (unit / 'near-miss').mkdir(parents=True)
        (unit / 'near-miss/0x1000.cpp').write_text('// old\n')
        u = wq.claim(self.q, 'haiku-1', t=1_000_000.0, repo=self.tmp)
        moved = u['earlier_near_misses']
        self.assertTrue((moved / '0x1000.cpp').is_file())
        self.assertFalse((unit / 'near-miss/0x1000.cpp').exists())
        # A session resuming its own claim keeps its files where they are.
        (unit / 'near-miss/0x1000.cpp').write_text('// mine\n')
        u = wq.claim(self.q, 'haiku-1', t=1_000_100.0, repo=self.tmp)
        self.assertTrue((unit / 'near-miss/0x1000.cpp').is_file())

    def test_near_miss_paths_derive_from_the_queue_in_use(self):
        unit = self.tmp / '.local/tasks/g/g-u0'
        (unit / 'near-miss').mkdir(parents=True)
        (unit / 'near-miss/0x1000.cpp').write_text('// old\n')
        # A scratch copy of the queue, outside any .local/queue/ layout, claims without a repo
        # argument: the unit dirs resolve against the copy, so the real unit keeps its files.
        scratch = self.tmp / 'scratch-queue'
        shutil.copytree(self.q, scratch)
        self.assertEqual(wq.queue_repo(scratch), scratch)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(wq.main(['--queue-dir', str(scratch), 'next', '--worker', 'haiku-1']), 0)
        self.assertTrue((unit / 'near-miss/0x1000.cpp').is_file())
        # The queue in its own repository resolves against that repository, again with no argument.
        self.assertEqual(wq.queue_repo(self.q), self.tmp)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(wq.main(['--queue-dir', str(self.q), 'next', '--worker', 'haiku-1']), 0)
        self.assertFalse((unit / 'near-miss/0x1000.cpp').exists())
        self.assertEqual(len(list((unit / 'near-miss').glob('earlier-*/0x1000.cpp'))), 1)

    def test_cli_release(self):
        wq.claim(self.q, 'haiku-2')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = wq.main(['--queue-dir', str(self.q), 'release', '.local/tasks/g/g-u0', '--worker', 'haiku-2'])
        self.assertEqual(code, 0)
        self.assertIn('released', out.getvalue())


class Profiles(unittest.TestCase):
    def test_default_is_cheap_and_roles_are_complete(self):
        self.assertEqual(profiles.DEFAULT, 'cheap')
        for name in ('cheap', 'full', 'claude-low'):
            p = profiles.get(name)
            self.assertEqual(set(p['roles']), set(profiles.ROLES))
            for entry in p['roles'].values():
                self.assertTrue({'provider', 'model', 'harness'} <= entry.keys())
            self.assertTrue(p['cost'].startswith(name + ':'))
        self.assertIn('terra', profiles.role('claude-low', 'reviewer')['model'])
        self.assertIn('sol', profiles.role('claude-low', 'strong')['model'])
        with self.assertRaises(ValueError):
            profiles.get('nope')

    def test_cli_prints_a_cost_line_per_profile(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            profiles.main([])
        self.assertEqual(len(out.getvalue().splitlines()), len(profiles.PROFILES))
        self.assertIn('[default]', out.getvalue())


class Friction(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        q = self.tmp / '.local/queue/small'
        q.mkdir(parents=True)
        (q / 'queue.tsv').write_text('')
        recs = [
            {'worker': 'haiku-1', 'profile': 'cheap', 'queue_unit': 'u1', 'rva': '0x1', 'result': 'pass', 'attempts': 2},
            {'worker': 'haiku-1', 'profile': 'cheap', 'queue_unit': 'u1', 'rva': '0x2', 'result': 'fail', 'attempts': 3,
             'reason': 'function-size-mismatch size 20/19'},
            {'worker': 'haiku-1', 'profile': 'cheap', 'queue_unit': 'u1', 'unit': 'a.cpp', 'claimed': '2026-01-01T00:00:00Z',
             'recorded': '2026-01-01T00:10:00Z', 'friction': 'stale near-miss file'},
            {'worker': 'luna56-medium-1', 'queue_unit': 'u2', 'rva': '0x3', 'result': 'fail', 'attempts': 3,
             'reason': 'function-size-mismatch size 31/30'},
            {'worker': 'luna56-medium-1', 'queue_unit': 'u2', 'unit': 'b.cpp'},
        ]
        (q / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in recs))
        rv = self.tmp / '.local/reviews'
        rv.mkdir(parents=True)
        (rv / 'review-x.md').write_text(review_text('review-x', [(0x10, 4, 'd' * 64, 'reject', 'none')]))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_report_counts_per_profile_and_model(self):
        rep = friction.summarise(self.tmp, now=0)
        cheap = rep['by_profile']['cheap']
        # The luna lines carry no profile; the queue directory says cheap.
        self.assertEqual((cheap['functions'], cheap['passed']), (3, 1))
        self.assertEqual(rep['by_model']['haiku']['median_minutes_per_unit'], 10.0)
        self.assertEqual(rep['by_model']['luna56-medium']['abandoned_units'], 1)
        self.assertEqual(rep['top_failure_messages'][0], ('fail: function-size-mismatch size N/N', 2))
        self.assertIn(('check provenance failed', 1), rep['rejects_by_reason'])
        self.assertIsNotNone(rep['cheap_flag'])  # 1/3 is below the threshold
        self.assertIn('below', friction.render(rep))

    def test_write_logs_the_event(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            friction.main(['--root', str(self.tmp), '--write'])
        fdir = self.tmp / '.local/flow'
        self.assertEqual(len(list(fdir.glob('friction-*.md'))), 1)
        self.assertIn('"event": "friction"', (fdir / 'events.jsonl').read_text())


class ReviewCompare(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, name, blocks):
        path = self.tmp / f'{name}.md'
        path.write_text(review_text(name, blocks))
        return str(path)

    def test_missed_and_stricter_are_told_apart_for_each_candidate(self):
        d = 'd' * 64
        ref = self.write('opus', [(0x10, 4, d, 'reject', 'none'), (0x20, 8, d, 'approve', 'none'), (0x30, 8, d, 'approve', 'none')])
        son = self.write('sonnet', [(0x10, 4, d, 'approve', 'none'), (0x20, 8, d, 'reject', 'none'), (0x30, 8, d, 'approve', 'none')])
        ter = self.write('terra', [(0x10, 4, d, 'reject', 'none'), (0x20, 8, d, 'approve', 'none')])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = review_compare.main(['--json', '--set', 'opus', ref, '--set', 'sonnet', son, '--set', 'terra', ter])
        res = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        s, t = res[0]['summary'], res[1]['summary']
        self.assertEqual((s['missed'], s['stricter'], s['agree'], s['caught']), (1, 1, 1, 0))
        self.assertEqual((t['agree'], t['caught'], t['only-reference']), (2, 1, 1))
        self.assertNotIn(f'## {BUILD}', out.getvalue())  # verdicts and counts only

    def test_full_agreement_exits_zero(self):
        d = 'd' * 64
        a = self.write('a', [(0x10, 4, d, 'approve', 'none')])
        b = self.write('b', [(0x10, 4, d, 'approve', 'none')])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(review_compare.main(['--reference', a, '--candidate', b]), 0)


if __name__ == '__main__':
    unittest.main()
