"""Tests for tools/work_queue.py: atomic claims across processes, stale-claim takeover, results
and per-model statistics. All inputs are synthetic."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import work_queue as wq  # noqa: E402

TOOL = ROOT / 'tools' / 'work_queue.py'


def write_queue(qdir, n):
    qdir.mkdir(parents=True, exist_ok=True)
    lines = ['# unit dir\tsources\tfunctions\tbudget']
    for i in range(n):
        lines.append(f'.local/tasks/g/g-u{i}\treconstruction/misc/U{i}.h,reconstruction/misc/U{i}.cpp\t0x{i + 1:x}000\t3')
    (qdir / 'queue.tsv').write_text('\n'.join(lines) + '\n')


class Queue(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.q = self.tmp / 'q'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_two_processes_never_get_the_same_unit(self):
        write_queue(self.q, 1)
        # Many racing processes for one unit: exactly one gets it, the rest see EMPTY.
        procs = [subprocess.Popen([sys.executable, str(TOOL), '--queue-dir', str(self.q), 'next', '--worker', f'w-{i}'],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True) for i in range(8)]
        outs = [p.communicate()[0].strip() for p in procs]
        self.assertEqual(sum(o == '.local/tasks/g/g-u0' for o in outs), 1, outs)
        self.assertTrue(all(o == '.local/tasks/g/g-u0' or o.startswith('EMPTY') for o in outs), outs)

    def test_two_processes_split_two_units(self):
        write_queue(self.q, 2)
        procs = [subprocess.Popen([sys.executable, str(TOOL), '--queue-dir', str(self.q), 'next', '--worker', f'w-{i}'],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True) for i in range(2)]
        outs = sorted(p.communicate()[0].strip() for p in procs)
        self.assertEqual(outs, ['.local/tasks/g/g-u0', '.local/tasks/g/g-u1'])

    def test_stale_claim_is_taken_over_and_fresh_one_is_not(self):
        write_queue(self.q, 1)
        t0 = 1_000_000.0
        self.assertEqual(wq.claim(self.q, 'luna-1', t=t0)['key'], 'g-u0')
        self.assertIsNone(wq.claim(self.q, 'haiku-1', t=t0 + wq.STALE_SECONDS - 1))
        u = wq.claim(self.q, 'haiku-1', t=t0 + wq.STALE_SECONDS + 1)
        self.assertEqual(u['key'], 'g-u0')
        self.assertEqual(json.loads((self.q / 'claims/g-u0.lock').read_text())['worker'], 'haiku-1')
        self.assertEqual([p.name for p in (self.q / 'claims').iterdir()], ['g-u0.lock'])

    def test_a_restarted_session_resumes_its_own_claim(self):
        write_queue(self.q, 2)
        self.assertEqual(wq.claim(self.q, 'luna-1')['key'], 'g-u0')
        self.assertEqual(wq.claim(self.q, 'luna-1')['key'], 'g-u0')
        self.assertEqual(wq.claim(self.q, 'luna-2')['key'], 'g-u1')

    def test_done_records_releases_and_moves_on(self):
        write_queue(self.q, 2)
        wq.claim(self.q, 'luna56-medium-1')
        recs = wq.finish(self.q, '.local/tasks/g/g-u0/', [
            '{"rva": "0x1000", "result": "pass", "reason": "all-checks-passed", "attempts": 2}',
            '{"task": "g-u0", "unit": "reconstruction/misc/U0.cpp", "attempts": 2, "blocker": null}'])
        self.assertEqual({r['worker'] for r in recs}, {'luna56-medium-1'})
        self.assertFalse((self.q / 'claims/g-u0.lock').exists())
        lines = (self.q / 'results.jsonl').read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(wq.claim(self.q, 'luna56-medium-1')['key'], 'g-u1')
        self.assertEqual([s for s, _, _ in wq.status(self.q)], ['done', 'claimed'])

    def test_done_refuses_bad_lines_and_unknown_units(self):
        write_queue(self.q, 1)
        wq.claim(self.q, 'w-1')
        with self.assertRaisesRegex(wq.QueueError, 'not one JSON object'):
            wq.finish(self.q, '.local/tasks/g/g-u0', ['not json'])
        with self.assertRaisesRegex(wq.QueueError, 'needs'):
            wq.finish(self.q, '.local/tasks/g/g-u0', ['{"x": 1}'])
        with self.assertRaisesRegex(wq.QueueError, 'not a unit'):
            wq.finish(self.q, '.local/tasks/g/g-zz', ['{"unit": "x"}'])
        self.assertFalse((self.q / 'results.jsonl').exists())
        with self.assertRaisesRegex(wq.QueueError, 'worker'):
            wq.claim(self.q, 'bad label!')

    def test_fallback_claims_only_failed_and_preserves_first_results(self):
        self.q.mkdir(parents=True)
        (self.q / 'queue.tsv').write_text('unit-a\ta.cpp\t0x1000,0x1010\t3\nunit-b\tb.cpp\t0x2000\t3\n')
        wq.claim(self.q, 'haiku-1', profile='cheap')
        wq.finish(self.q, 'unit-a', ['{"rva":"0x1000","result":"pass"}',
                                      '{"rva":"0x1010","result":"fail"}', '{"unit":"a"}'])
        wq.claim(self.q, 'haiku-1', profile='cheap')
        wq.finish(self.q, 'unit-b', ['{"rva":"0x2000","result":"pass"}', '{"unit":"b"}'])
        # Existing results have no tier; they still belong to the first tier.
        path = self.q / 'results.jsonl'
        path.write_text(''.join(json.dumps({k: v for k, v in json.loads(line).items() if k != 'tier'}) + '\n'
                                for line in path.read_text().splitlines()))
        self.assertEqual(wq.claim(self.q, 'terra-1', profile='claude-low', tier='fallback')['key'], 'unit-a')
        self.assertEqual(wq.unpassed(self.q, wq.find_unit(self.q, 'unit-a')), ['0x1010'])
        with self.assertRaises(wq.QueueError):
            wq.finish(self.q, 'unit-a', ['{"rva":"0x1000","result":"fail"}'], tier='fallback')
        wq.finish(self.q, 'unit-a', ['{"rva":"0x1010","result":"pass"}', '{"unit":"a"}'], tier='fallback')
        self.assertIsNone(wq.claim(self.q, 'terra-2', profile='claude-low', tier='fallback'))
        self.assertEqual(json.loads(path.read_text().splitlines()[-2])['tier'], 'fallback')
        with self.assertRaises(wq.QueueError):
            wq.claim(self.q, 'other', profile='cheap', tier='fallback')

    def test_fallback_budget_uses_unpassed_count(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader('attempt_test', str(ROOT / 'tools/verifier/attempt'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        attempt = importlib.util.module_from_spec(spec)
        loader.exec_module(attempt)
        self.q.mkdir(parents=True)
        (self.q / 'queue.tsv').write_text('unit-a\ta.cpp\t0x1,0x2,0x3\t3\n')
        wq.claim(self.q, 'haiku-1')
        wq.finish(self.q, 'unit-a', ['{"rva":"0x1","result":"pass"}',
                                      '{"rva":"0x2","result":"fail"}',
                                      '{"rva":"0x3","result":"fail"}'])
        wq.claim(self.q, 'terra-1', profile='claude-low', tier='fallback')
        self.assertEqual(attempt.fallback_budget('unit-a', self.q), 16)

    def test_add_units_of_a_group_with_remaining_budget(self):
        repo = self.tmp / 'repo'
        g = repo / '.local/tasks/g'
        for i, used in ((0, 0), (1, 2)):
            d = g / f'g-u{i}'
            d.mkdir(parents=True)
            (d / 'task.json').write_text(json.dumps({'compiled': f'reconstruction/misc/U{i}.cpp', 'max_attempts': 4,
                                                     'functions': [{'rva': f'0x{i + 1}0'}]}))
            (d / 'attempts.jsonl').write_text(''.join(json.dumps({'counted': True}) + '\n' for _ in range(used))
                                              + json.dumps({'counted': False}) + '\n')
        (g / 'group.json').write_text(json.dumps({'units': [{'dir': 'g-u1'}, {'dir': 'g-u0'}]}))
        self.assertEqual(wq.add(self.q, ['.local/tasks/g'], repo), ['.local/tasks/g/g-u1', '.local/tasks/g/g-u0'])
        self.assertEqual(wq.add(self.q, ['.local/tasks/g/g-u0'], repo), [])  # never twice
        units = wq.read_queue(self.q)
        self.assertEqual([(u['key'], u['budget']) for u in units], [('g-u1', 2), ('g-u0', 4)])
        self.assertEqual(units[0]['sources'], ['reconstruction/misc/U1.h', 'reconstruction/misc/U1.cpp'])

    def test_empty_and_stats_per_worker_and_model(self):
        write_queue(self.q, 2)
        for worker in ('luna56-medium-1', 'luna56-medium-2'):
            wq.claim(self.q, worker)
        wq.finish(self.q, '.local/tasks/g/g-u0', ['{"rva": "0x1", "result": "pass", "attempts": 1}', '{"unit": "a"}'])
        wq.finish(self.q, '.local/tasks/g/g-u1', ['{"rva": "0x2", "result": "fail", "attempts": 3}', '{"unit": "b"}'])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(wq.main(['--queue-dir', str(self.q), 'next', '--worker', 'haiku-1']), 0)
        self.assertEqual(out.getvalue().strip(), 'EMPTY')
        s = wq.stats(self.q)
        self.assertEqual(s['worker']['luna56-medium-1']['pass_rate'], 1.0)
        m = s['model']['luna56-medium']
        self.assertEqual((m['functions'], m['passed'], m['units'], m['attempts_per_function']), (2, 1, 2, 2.0))


if __name__ == '__main__':
    unittest.main()
