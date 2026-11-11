"""Cost ledger: transcript parsing, idempotent ingest, allocation checks, hooks and the page section."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cost_hooks
import cost_ledger as cl
from build_site import cost_section

B = 'synthetic-build'
F1, F2 = f'{B}:0x1000', f'{B}:0x2000'
PROGRESS = {'functions': [dict(build_id=B, rva=0x1000, status='matched', name='One'),
                          dict(build_id=B, rva=0x2000, status='mapped', name='Two')]}


def line(mid, model='model-x', inp=1, cw=10, cr=100, out=5, tool=None, ts='2030-01-01T00:00:00Z'):
    content = [{'type': 'tool_use', 'id': tool, 'name': 'Bash', 'input': {}}] if tool else []
    return json.dumps({'timestamp': ts, 'message': {
        'id': mid, 'role': 'assistant', 'model': model, 'content': content,
        'usage': {'input_tokens': inp, 'cache_creation_input_tokens': cw,
                  'cache_read_input_tokens': cr, 'output_tokens': out}}})


class CostLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, name, lines):
        path = self.dir / name
        path.write_text('\n'.join(lines + ['not json', json.dumps({'type': 'user', 'message': {'role': 'user'}})]) + '\n')
        return path

    def test_parse_counts_each_message_once(self):
        path = self.transcript('agent-a0000000000000001.jsonl', [
            line('m1', tool='t1'), line('m1', tool='t1'), line('m2', out=7, ts='2030-01-01T00:01:40Z')])
        parsed = cl.parse_transcript(path)
        self.assertEqual(parsed['messages'], 2)
        self.assertEqual(parsed['tool_uses'], 1)
        self.assertEqual(parsed['tokens'], {'input': 2, 'cache_creation': 20, 'cache_read': 200, 'output': 12})
        self.assertEqual(parsed['agent_wall_seconds'], 100)
        self.assertEqual(parsed['date'], '2030-01-01')

    def test_reingest_replaces_record(self):
        ledger = cl.empty_ledger()
        path = self.transcript('a0000000000000002.output', [line('m1')])
        cl.ingest(ledger, path, 'drafter', 't', 'draft', cl.parse_allocs([f'{F1}=1']), complete=False)
        path.write_text(line('m1') + '\n' + line('m2') + '\n')
        cl.ingest(ledger, path, 'drafter', 't', 'draft', cl.parse_allocs([f'{F1}=1']))
        self.assertEqual(len(ledger['records']), 1)
        self.assertEqual(ledger['records'][0]['id'], 'agent-a0000000000000002')
        self.assertEqual(ledger['records'][0]['messages'], 2)
        self.assertTrue(ledger['records'][0]['complete'])
        cl.validate(ledger, PROGRESS)

    def test_ingest_dir_marks_unmapped_and_skips_empty(self):
        self.transcript('agent-a0000000000000003.jsonl', [line('m1')])
        self.transcript('agent-a0000000000000004.jsonl', [line('m2')])
        (self.dir / 'b1234.output').write_text('shell log\n')
        ledger = cl.empty_ledger()
        mapping = {'a0000000000000003': {'role': 'engineer', 'task': 'tool', 'stage': 'tooling'}}
        done, unmapped = cl.ingest_dir(ledger, self.dir, mapping)
        self.assertEqual(unmapped, ['a0000000000000004'])
        self.assertEqual(len(done), 2)
        roles = sorted(r['role'] for r in ledger['records'])
        self.assertEqual(roles, ['engineer', 'unknown'])
        cl.validate(ledger, PROGRESS)

    def test_parse_allocs_equal_split_fills_remainder(self):
        allocs = cl.parse_allocs([F1, F2, 'overhead=0.5'])
        self.assertEqual({a['target']: a['share'] for a in allocs}, {F1: 0.25, F2: 0.25, 'overhead': 0.5})
        self.assertEqual(cl.parse_allocs(None), [{'target': 'overhead', 'share': 1.0}])
        self.assertEqual(cl.normalize_target(f'{B}:4096'), F1)

    def record(self, **kw):
        return cl.make_record('r1', 'engineer', 't', 'tooling', [{'target': 'overhead', 'share': 1.0}], **kw)

    def test_validate_rejects_bad_ledgers(self):
        cases = {
            'sum to 1': dict(allocations=[{'target': F1, 'share': 0.5}]),
            'not overhead or a function': dict(allocations=[{'target': f'{B}:0x9999', 'share': 1.0}]),
            'bad role': dict(role='manager'),
            'bad stage': dict(stage='lunch'),
            'local path': dict(source='read from /Users/someone/x.jsonl'),
            'int >= 0': dict(tokens={'input': -1, 'cache_creation': 0, 'cache_read': 0, 'output': 0}),
            'unexpected fields': dict(prompt='secret text'),
            'boat_seconds': dict(boat_seconds='lots'),
        }
        for message, change in cases.items():
            with self.subTest(message):
                ledger = cl.empty_ledger()
                record = self.record()
                record.update(change)
                ledger['records'].append(record)
                with self.assertRaisesRegex(ValueError, message):
                    cl.validate(ledger, PROGRESS)
        ledger = cl.empty_ledger()
        ledger['records'] = [self.record(), self.record()]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            cl.validate(ledger, PROGRESS)
        ledger = cl.empty_ledger()
        ledger['profiles'] = {'p': [f'{B}:0x7777']}
        with self.assertRaisesRegex(ValueError, 'unknown target'):
            cl.validate(ledger, PROGRESS)

    def synthetic_ledger(self):
        ledger = cl.empty_ledger()
        ledger['profiles'] = {'second-batch': [F1]}
        tokens = {'input': 10, 'cache_creation': 100, 'cache_read': 1000, 'output': 40}
        ledger['records'] = [
            cl.make_record('a', 'drafter', 'd', 'draft', [{'target': F1, 'share': 1.0}], tokens=dict(tokens),
                           boat_seconds=360),
            cl.make_record('b', 'engineer', 'e', 'tooling', [{'target': F1, 'share': 0.25}, {'target': 'overhead', 'share': 0.75}],
                           tokens=dict(tokens), boat_seconds=100,
                           boat_allocations=[{'target': 'overhead', 'share': 1.0}], estimated=True)]
        return cl.validate(ledger, PROGRESS)

    def test_report_and_estimate_split_shares(self):
        ledger = self.synthetic_ledger()
        direct = cl.per_target(ledger)
        self.assertEqual(direct[F1]['tokens']['output'], 50)
        self.assertEqual(direct[F1]['boat_seconds'], 360)
        self.assertEqual(direct['overhead']['boat_seconds'], 100)
        out = io.StringIO()
        cl.report(ledger, PROGRESS, out=out)
        self.assertIn('orchestrator tokens: not captured', out.getvalue())
        self.assertIn('tooling', out.getvalue())
        out = io.StringIO()
        cl.estimate(ledger, PROGRESS, 10, 'second-batch', out=out)
        self.assertIn('output=500', out.getvalue())
        self.assertIn('boat=1.0 h', out.getvalue())
        self.assertIn('biased toward', out.getvalue())

    def test_money_lists_missing_prices(self):
        ledger = self.synthetic_ledger()
        out = io.StringIO()
        cl.report(ledger, PROGRESS, {'models': {}, 'boat_per_hour': None}, out=out)
        self.assertIn('cannot price', out.getvalue())
        rates = {'input': 1.0, 'cache_creation': 1.0, 'cache_read': 1.0, 'output': 1.0}
        amount, missing = cl.money({'m': {'input': 1e6, 'cache_creation': 0, 'cache_read': 0, 'output': 0}},
                                   3600, {'models': {'m': rates}, 'boat_per_hour': 2.0})
        self.assertEqual((amount, missing), (3.0, []))

    def test_hook_queue_and_flush(self):
        pending = self.dir / 'costs/pending.jsonl'
        cost_hooks.record_boat('task-1', 'confirm', 90, 120, [F1, F2], pending=pending)
        cost_hooks.record_boat('task-2', 'draft', 30, None, [], pending=pending)
        ledger = cl.empty_ledger()
        self.assertEqual(cl.flush(ledger, pending), 2)
        self.assertEqual(pending.read_text(), '')
        cl.validate(ledger, PROGRESS)
        by_task = {r['task']: r for r in ledger['records']}
        self.assertEqual(by_task['task-1']['allocations'], [{'target': F1, 'share': 0.5}, {'target': F2, 'share': 0.5}])
        self.assertEqual(by_task['task-1']['boat_seconds'], 90)
        self.assertEqual(by_task['task-2']['allocations'], [{'target': 'overhead', 'share': 1.0}])
        self.assertEqual(cl.flush(ledger, pending), 0)

    def test_cli_round_trip(self):
        ledger_path, progress_path = self.dir / 'costs.json', self.dir / 'progress.json'
        progress_path.write_text(json.dumps(PROGRESS))
        path = self.transcript('agent-a0000000000000005.jsonl', [line('m1')])
        base = ['--ledger', str(ledger_path), '--progress', str(progress_path)]
        self.assertEqual(cl.main(base + ['ingest', '--transcript', str(path), '--role', 'reviewer', '--task', 'r',
                                         '--stage', 'review', '--alloc', f'{F1}=1']), 0)
        self.assertEqual(cl.main(base + ['add-compute', '--task', 'c', '--seconds', '10', '--alloc', F1]), 0)
        self.assertEqual(cl.main(base + ['validate']), 0)
        self.assertEqual(len(json.loads(ledger_path.read_text())['records']), 2)
        self.assertEqual(cl.main(base + ['ingest', '--transcript', str(path), '--role', 'reviewer', '--task', 'r',
                                         '--stage', 'review', '--alloc', f'{B}:0x5555=1']), 1)

    def test_page_section(self):
        ledger = self.synthetic_ledger()
        html = cost_section(PROGRESS, ledger)
        self.assertIn('Cost so far', html)
        self.assertIn('subagents only; orchestrator tokens are not captured', html)
        self.assertIn('Average direct cost per accepted function (1)', html)
        self.assertIn('0.13 h', html)
        self.assertIn('No cost ledger recorded yet', cost_section(PROGRESS, None))

    def test_tracked_ledger_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        ledger = json.loads((root / 'data/costs.json').read_text())
        cl.validate(ledger, json.loads((root / 'data/progress.json').read_text()))
        prices = json.loads((root / 'data/prices.json').read_text())
        self.assertIn('ASSUMPTIONS', prices['comment'])


if __name__ == '__main__':
    unittest.main()
