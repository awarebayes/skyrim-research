"""tools/check.py validates the cost ledger against the inventory, in the normal and --staged paths."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check  # noqa: E402
from check_source_digest import source_digest_cache  # noqa: E402

PROGRESS = json.loads((ROOT / 'data/progress.json').read_text())


def ledger_for(target):
    return {'schema_version': 1, 'note': 'synthetic', 'profiles': {}, 'records': [{
        'id': 'agent-synthetic', 'date': '2000-01-01', 'role': 'drafter', 'model': None, 'task': 'synthetic',
        'stage': 'draft', 'tokens': {'input': 1, 'cache_creation': 0, 'cache_read': 0, 'output': 1},
        'messages': 1, 'tool_uses': 0, 'boat_seconds': None, 'boat_wall_seconds': None,
        'agent_wall_seconds': None, 'allocations': [{'target': target, 'share': 1}], 'boat_allocations': None,
        'estimated': False, 'complete': True, 'source': 'synthetic test'}]}


class CheckCostsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'data').mkdir()
        fn = PROGRESS['functions'][0]
        self.present = f'{fn["build_id"]}:0x{fn["rva"]:x}'

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, ledger):
        (self.root / check.COST_LEDGER).write_text(json.dumps(ledger))

    def test_allocation_to_inventory_function_passes(self):
        self.write(ledger_for(self.present))
        check.check_costs(self.root, PROGRESS)

    def test_allocation_to_missing_function_fails(self):
        self.write(ledger_for(f'{PROGRESS["target_build_id"]}:0x7ffffff0'))
        with self.assertRaisesRegex(ValueError, 'Cost ledger data/costs.json: .*not overhead or a function'):
            check.check_costs(self.root, PROGRESS)

    def test_function_removed_from_inventory_fails(self):
        self.write(ledger_for(self.present))
        progress = copy.deepcopy(PROGRESS)
        progress['functions'] = progress['functions'][1:]
        with self.assertRaisesRegex(ValueError, 'Cost ledger'):
            check.check_costs(self.root, progress)

    def test_malformed_ledger_fails(self):
        (self.root / check.COST_LEDGER).write_text(json.dumps({'schema_version': 2, 'records': []}))
        with self.assertRaisesRegex(ValueError, 'schema_version'):
            check.check_costs(self.root, PROGRESS)

    def test_real_ledger_passes(self):
        check.check_costs(ROOT, PROGRESS)

    def test_both_load_paths_check_the_ledger(self):
        for staged in (False, True):
            # Each load reads a frozen snapshot, just like check.main's cache scope.
            with self.subTest(staged=staged), mock.patch.object(check, 'check_costs') as called, source_digest_cache():
                check.load(staged=staged)
                self.assertEqual(called.call_count, 1)


if __name__ == '__main__':
    unittest.main()
