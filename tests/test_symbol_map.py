"""Symbol-map versions: additions keep match records valid, any change to what they used does not.

Built on the match-gate fixture, so the record under test holds reports the real comparator wrote
for the synthetic function, and `check` is the full repository validation CI runs.
"""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import symbol_map as sm  # noqa: E402
from test_match_gate import MAP, RECORD, GateFixture, sha256  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402

HISTORY = sm.history_name(MAP)
FAR = 0x5000  # outside every fixture range


class SymbolMapFixture(GateFixture):
    def setUp(self):
        super().setUp()
        # The fixture writes the map without the final newline; the history needs canonical bytes.
        self.write(MAP, sm.serialize(json.loads((self.root / MAP).read_text())))
        self.record = self.make_record()
        self.save_record()
        self.pinned = self.record['symbol_map']['sha256']

    def incoming(self, symbols, folds=()):
        return {'schema': 1, 'build_id': 'synthetic-fixture', 'symbols': symbols, 'folds': [list(g) for g in folds]}

    def add(self, symbols, folds=(), root=None, **kw):
        return sm.apply_change(root or self.root, MAP, self.incoming(symbols, folds), **kw)

    def current_map(self):
        return json.loads((self.root / MAP).read_text())

    def history(self):
        return json.loads((self.root / HISTORY).read_text())

    def write_history(self, history):
        self.write(HISTORY, sm.serialize(history))


class AdditionTests(SymbolMapFixture, unittest.TestCase):
    def test_unrelated_addition_keeps_record_valid(self):
        self.add({'Unrelated': {'rva': FAR, 'size': 8}})
        self.assertNotEqual(sha256((self.root / MAP).read_bytes()), self.pinned)
        self.check()

    def test_successive_additions_keep_record_valid(self):
        self.add({'First': {'rva': FAR, 'size': None}})
        self.add({'Second': {'rva': FAR + 0x10, 'size': 4}})
        self.assertEqual(len(self.history()['versions']), 3)
        self.check()

    def test_identical_existing_entry_is_not_a_change(self):
        same = self.current_map()['symbols']
        summary = self.add(dict(same, Extra={'rva': FAR, 'size': None}))
        self.assertEqual((summary['added'], summary['changed']), (['Extra'], []))
        self.check()

    def test_record_on_current_map_without_history_is_unchanged_behaviour(self):
        self.assertFalse((self.root / HISTORY).exists())
        self.check()

    def test_non_canonical_map_without_history_is_refused(self):
        self.write(MAP, json.dumps(self.current_map()))
        with self.assertRaisesRegex(ValueError, 'not in canonical form'):
            self.add({'Unrelated': {'rva': FAR, 'size': None}})


    def test_thread_local_entry_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'must be {rva, size}'):
            self.add({'tVar': {'kind': 'thread-local', 'tls_offset': 8, 'size': None}})
        smap = self.current_map()
        smap['symbols']['tVar'] = {'kind': 'thread-local', 'tls_offset': 8, 'size': None}
        with self.assertRaisesRegex(ValueError, 'thread-local entries'):
            sm.check_map(smap)

class ChangeTests(SymbolMapFixture, unittest.TestCase):
    def test_changed_entry_is_refused_without_flag(self):
        with self.assertRaisesRegex(ValueError, f'changes existing entries: {fx.CALLEE}'):
            self.add({fx.CALLEE: {'rva': fx.LAYOUT[fx.CALLEE] + 4, 'size': None}})
        self.assertFalse((self.root / HISTORY).exists())

    def test_changed_entry_with_flag_makes_record_stale(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        summary = self.add({fx.CALLEE: {'rva': fx.LAYOUT[fx.CALLEE], 'size': None}}, allow_change=True)
        self.assertEqual([p for p, _ in summary['stale_records']], [RECORD])
        self.assertGateRejects('symbol map hash is stale: an entry of the pinned map version was changed')

    def test_change_leaves_versions_without_the_entry_valid(self):
        # A record pinned to a version that predates the changed entry stays valid.
        self.add({'Later': {'rva': FAR, 'size': None}})
        self.add({'Later': {'rva': FAR + 0x20, 'size': None}}, allow_change=True)
        versions = self.history()['versions']
        self.assertNotIn('superseded', versions[0])
        self.assertTrue(versions[1]['superseded'])
        self.check()

    def test_removed_entry_is_refused_without_flag(self):
        with self.assertRaisesRegex(ValueError, f'removes entries: {fx.OTHER_CALLEE}'):
            self.add({}, remove=[fx.OTHER_CALLEE])

    def test_removed_entry_with_flag_makes_record_stale(self):
        summary = self.add({}, remove=[fx.OTHER_CALLEE], allow_change=True)
        self.assertEqual(len(summary['stale_records']), 1)
        self.assertGateRejects('symbol map hash is stale')

    def test_hand_edited_entry_fails_the_history(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        smap = self.current_map()
        smap['symbols'][fx.CALLEE]['size'] = None
        self.write(MAP, sm.serialize(smap))
        self.assertGateRejects('changed outside tools/symbol_map.py|does not rebuild')

    def test_hand_edit_with_history_head_updated_still_fails(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        smap = self.current_map()
        smap['symbols'][fx.CALLEE]['size'] = None
        self.write(MAP, sm.serialize(smap))
        history = self.history()
        history['versions'][-1]['sha256'] = sha256((self.root / MAP).read_bytes())
        self.write_history(history)
        self.assertGateRejects('version 0 does not rebuild')

    def test_hand_removed_entry_fails_the_history(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        smap = self.current_map()
        del smap['symbols'][fx.OTHER_CALLEE]
        self.write(MAP, sm.serialize(smap))
        self.assertGateRejects('no longer has|changed outside')

    def test_reordered_map_fails(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        smap = self.current_map()
        smap['symbols'] = dict(reversed(list(smap['symbols'].items())))
        self.write(MAP, sm.serialize(smap))
        self.assertGateRejects('does not rebuild|changed outside tools/symbol_map.py')
        history = self.history()
        history['versions'][-1]['sha256'] = sha256((self.root / MAP).read_bytes())
        self.write_history(history)
        self.assertGateRejects('does not rebuild')

    def test_whitespace_change_fails(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        self.write(MAP, (self.root / MAP).read_bytes() + b' ')
        self.assertGateRejects('not in canonical form')

    def test_extended_fold_group_supersedes(self):
        with self.assertRaisesRegex(ValueError, 'names existing entries'):
            self.add({'Alias': {'rva': FAR, 'size': None}}, folds=[[fx.CALLEE, 'Alias']])


class ShadowTests(SymbolMapFixture, unittest.TestCase):
    def test_addition_at_existing_rva_is_refused(self):
        with self.assertRaisesRegex(ValueError, f'shares an address or range with existing entry {fx.CALLEE}'):
            self.add({'Shadow': {'rva': fx.LAYOUT[fx.CALLEE], 'size': None}})

    def test_addition_inside_existing_range_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'shares an address or range'):
            self.add({'Inside': {'rva': fx.LAYOUT[fx.FUNCTION] + 2, 'size': None}})

    def test_sized_addition_covering_existing_entry_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'shares an address or range'):
            self.add({'Cover': {'rva': fx.LAYOUT[fx.FUNCTION] - 8, 'size': 16}})

    def test_addition_at_function_makes_record_stale_even_when_forced(self):
        self.add({'Alias': {'rva': fx.LAYOUT[fx.FUNCTION], 'size': None}}, allow_change=True)
        self.assertGateRejects('added entry Alias lies at or in the function range')

    def test_addition_overlapping_function_makes_record_stale(self):
        self.add({'Cover': {'rva': fx.LAYOUT[fx.FUNCTION] - 4, 'size': 8}}, allow_change=True)
        self.assertGateRejects('added entry Cover lies at or in the function range')

    def test_same_name_different_value_is_a_change(self):
        with self.assertRaisesRegex(ValueError, 'changes existing entries'):
            self.add({fx.FUNCTION: {'rva': fx.LAYOUT[fx.FUNCTION], 'size': None}})

    def test_added_entries_sharing_rva_need_a_fold(self):
        with self.assertRaisesRegex(ValueError, 'share an RVA without a fold group'):
            self.add({'A': {'rva': FAR, 'size': None}, 'B': {'rva': FAR, 'size': None}})
        self.add({'A': {'rva': FAR, 'size': None}, 'B': {'rva': FAR, 'size': None}}, folds=[['A', 'B']])
        self.check()

    def test_image_base_addition_makes_record_stale(self):
        self.add({'__ImageBase': {'rva': 0, 'size': None}}, allow_change=True)
        self.assertGateRejects('__ImageBase was added')

    def test_function_with_funclets_is_not_carried(self):
        for run in self.record['runs']:
            run['report']['coverage']['funclet_sections'] = 1
        self.save_record()
        self.check()
        self.add({'Far': {'rva': FAR, 'size': None}}, allow_change=True)
        self.assertGateRejects('has funclets')

    def test_eh_handler_addition_with_handler_data_is_not_carried(self):
        for run in self.record['runs']:
            run['report']['coverage']['eh']['handlers'] = {'__CxxFrameHandler3': 1}
        self.save_record()
        self.check()
        self.add({'__GSHandlerCheck_EH': {'rva': FAR, 'size': None}}, allow_change=True)
        self.assertGateRejects('EH handler name was added')


class DuplicateKeyTests(SymbolMapFixture, unittest.TestCase):
    def test_duplicate_key_in_map_fails(self):
        text = (self.root / MAP).read_text()
        entry = f'"{fx.CALLEE}": {{"rva": {fx.LAYOUT[fx.CALLEE] + 4}, "size": null}},\n    '
        self.write(MAP, text.replace(f'"{fx.CALLEE}"', entry + f'"{fx.CALLEE}"', 1))
        self.assertGateRejects('duplicate JSON key')

    def test_duplicate_key_in_history_fails(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        text = (self.root / HISTORY).read_text()
        self.write(HISTORY, text.replace('"schema": 1,', '"schema": 1, "schema": 1,', 1))
        self.assertGateRejects('duplicate JSON key')

    def test_duplicate_key_in_incoming_is_refused(self):
        source = self.root / 'incoming.json'
        source.write_text('{"schema": 1, "build_id": "synthetic-fixture", "symbols": '
                          '{"X": {"rva": 1, "size": null}, "X": {"rva": 2, "size": null}}}')
        code = sm.main(['--root', str(self.root), 'add', '--map', MAP, '--from', str(source)])
        self.assertEqual(code, 1)


class ForgedHistoryTests(SymbolMapFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.add({'Unrelated': {'rva': FAR, 'size': None}})

    def test_version_with_wrong_names_fails(self):
        history = self.history()
        history['versions'][0]['added'].remove(fx.OTHER_CALLEE)
        history['versions'][1]['added'].append(fx.OTHER_CALLEE)
        self.write_history(history)
        self.assertGateRejects('version 0 does not rebuild')

    def test_forged_version_for_unknown_hash_fails(self):
        # A record pinned to a map that never existed cannot be vouched for by listing its hash.
        forged = 'f' * 64
        self.record['symbol_map']['sha256'] = forged
        self.save_record()
        self.assertGateRejects('not in the symbol map history')
        history = self.history()
        history['versions'].insert(1, {'sha256': forged, 'base': 0, 'added': []})
        history['versions'][-1]['base'] = 0
        self.write_history(history)
        self.assertGateRejects('version 1 does not rebuild')

    def test_forged_superseded_version_only_makes_records_stale(self):
        history = self.history()
        history['versions'][0]['superseded'] = True
        self.write_history(history)
        self.assertGateRejects('was changed or removed')

    def test_forward_base_fails(self):
        history = self.history()
        history['versions'][0]['base'] = 1
        self.write_history(history)
        self.assertGateRejects('base must name an earlier version')

    def test_name_added_twice_in_a_chain_fails(self):
        history = self.history()
        history['versions'][1]['added'].append(fx.CALLEE)
        self.write_history(history)
        self.assertGateRejects('adds a name its base already has')

    def test_history_for_another_map_fails(self):
        history = self.history()
        history['map'] = 'reports/other/symbol-map.json'
        self.write_history(history)
        self.assertGateRejects('needs schema 1, map')

    def test_orphan_history_fails(self):
        self.write('reports/other/symbol-map.history.json', (self.root / HISTORY).read_bytes())
        self.assertGateRejects('no symbol map')


class ImportTests(SymbolMapFixture, unittest.TestCase):
    def test_branch_record_survives_integration(self):
        """A record confirmed on a branch map stays valid after the branch's entries are merged."""
        branch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, branch)
        shutil.copytree(self.root, branch, dirs_exist_ok=True)
        self.add({'OnBranch': {'rva': FAR + 0x40, 'size': None}}, root=branch)
        branch_sha = sha256((branch / MAP).read_bytes())
        # The record is confirmed on the branch: its runs read the branch map.
        main_root, self.root = self.root, branch
        self.record = self.make_record()
        self.root = main_root
        self.assertEqual(self.record['symbol_map']['sha256'], branch_sha)
        self.add({'OnMain': {'rva': FAR, 'size': None}})
        self.save_record()
        self.assertGateRejects('not in the symbol map history')
        incoming = json.loads((branch / MAP).read_text())
        summary = sm.apply_change(self.root, MAP, incoming,
                                  other_history=json.loads((branch / HISTORY).read_text()))
        self.assertEqual(summary['imported'], 1)
        self.check()


class FuncletCarryForwardTests(unittest.TestCase):
    """carry_forward_problem for a function with funclets, from the ranges its reports give."""
    RVA, SIZE, FUNCLET = 0x1000, 0x40, (0x2000, 0x20)

    def state(self, added):
        symbols = {'Fn': {'rva': self.RVA, 'size': self.SIZE}, **added}
        return sm.MapState({'symbols': symbols}, 'x' * 64, {}, set())

    def reports(self, ranges=None, n=3, sections=1, total=0x20):
        cov = {'funclet_sections': sections, 'funclet_bytes_total': total}
        if ranges is not None:
            cov['funclet_ranges'] = ranges
        return [{'coverage': copy.deepcopy(cov)} for _ in range(n)]

    def problem(self, added, reports):
        return sm.carry_forward_problem(self.state(added), {'Fn'}, self.RVA, self.SIZE, reports)

    def test_addition_away_from_funclet_carries(self):
        self.assertIsNone(self.problem({'Far': {'rva': FAR, 'size': 8}}, self.reports([list(self.FUNCLET)])))

    def test_addition_in_funclet_range_refused(self):
        for entry in ({'rva': 0x2010, 'size': None}, {'rva': 0x1ff0, 'size': 0x20}, {'rva': 0x2000, 'size': None}):
            self.assertIn('funclet range', self.problem({'In': entry}, self.reports([list(self.FUNCLET)])))

    def test_addition_just_after_funclet_carries(self):
        self.assertIsNone(self.problem({'After': {'rva': 0x2020, 'size': 4}}, self.reports([list(self.FUNCLET)])))

    def test_reports_without_ranges_refused(self):
        self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}}, self.reports(None)))

    def test_disagreeing_ranges_refused(self):
        reports = self.reports([list(self.FUNCLET)])
        reports[2]['coverage']['funclet_ranges'] = [[0x3000, 0x20]]
        self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}}, reports))

    def test_ranges_short_of_compared_funclets_refused(self):
        # Two funclets compared but one range listed, or ranges not covering every funclet byte.
        self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}},
                                                  self.reports([list(self.FUNCLET)], sections=2)))
        self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}},
                                                  self.reports([list(self.FUNCLET)], total=0x30)))

    def test_malformed_range_refused(self):
        for bad in ([[0x2000]], [[0x2000, 0]], [['0x2000', 0x20]], [[-1, 0x20]], 'x'):
            self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}}, self.reports(bad)))


class CommandTests(SymbolMapFixture, unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOLS / 'symbol_map.py'), '--root', str(self.root), *args],
                              capture_output=True, text=True)

    def test_add_and_verify(self):
        source = self.root / 'incoming.json'
        source.write_text(json.dumps(self.incoming({'Unrelated': {'rva': FAR, 'size': None}})))
        dry = self.run_tool('add', '--map', MAP, '--from', str(source), '--dry-run')
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse((self.root / HISTORY).exists())
        done = self.run_tool('add', '--map', MAP, '--from', str(source))
        self.assertEqual(done.returncode, 0, done.stderr)
        verify = self.run_tool('verify', '--map', MAP)
        self.assertEqual(verify.returncode, 0, verify.stdout)
        self.assertIn(f'{RECORD}: carried', verify.stdout)

    def test_refused_change_exits_nonzero_and_writes_nothing(self):
        before = (self.root / MAP).read_bytes()
        source = self.root / 'incoming.json'
        source.write_text(json.dumps(self.incoming({fx.CALLEE: {'rva': 1, 'size': None}})))
        result = self.run_tool('add', '--map', MAP, '--from', str(source))
        self.assertEqual(result.returncode, 1)
        self.assertIn('--allow-change', result.stderr)
        self.assertEqual((self.root / MAP).read_bytes(), before)


class ProvenanceTests(unittest.TestCase):
    """Maps with `_provenance` (the real one) need a provenance entry per added name."""

    def base(self):
        return {'schema': 1, 'build_id': 'b', 'symbols': {'A': {'rva': 16, 'size': None}}, 'folds': [],
                '_provenance': {'database': 'd', 'entries': [{'name': 'A', 'note': 'n'}]}}

    def test_addition_without_provenance_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'no _provenance entry'):
            sm.plan(self.base(), {'build_id': 'b', 'symbols': {'B': {'rva': 32, 'size': None}}})

    def test_provenance_change_is_a_change(self):
        incoming = copy.deepcopy(self.base())
        incoming['_provenance']['entries'][0]['note'] = 'other'
        self.assertEqual(sm.plan(self.base(), incoming)['changed'], ['A'])

    def test_description_change_retires_every_version(self):
        incoming = copy.deepcopy(self.base())
        incoming['_provenance']['database'] = 'other'
        self.assertTrue(sm.plan(self.base(), incoming)['whole_map_changed'])

    def test_addition_keeps_rva_order_and_provenance_alignment(self):
        incoming = {'build_id': 'b', 'symbols': {'Z': {'rva': 8, 'size': None}},
                    '_provenance': {'entries': [{'name': 'Z'}]}}
        new = sm.plan(self.base(), incoming)['map']
        self.assertEqual(list(new['symbols']), ['Z', 'A'])
        self.assertEqual([e['name'] for e in new['_provenance']['entries']], ['Z', 'A'])
        self.assertEqual(sm.subset(new, {'A'}), self.base())


if __name__ == '__main__':
    unittest.main()
