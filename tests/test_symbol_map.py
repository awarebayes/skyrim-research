"""Symbol-map versions: additions keep match records valid, any change to what they used does not.

Built on the match-gate fixture, so the record under test holds reports the real comparator wrote
for the synthetic function, and `check` is the full repository validation CI runs.
"""
import ast
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import symbol_map as sm  # noqa: E402
from pecoff import EH_HANDLERS  # noqa: E402
from test_match_gate import MAP, RECORD, GateFixture, compiled_object, sha256  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402

HISTORY = sm.history_name(MAP)
FAR = 0x5000  # outside every fixture range
# map_audit fingerprint of tools/compare.py as audited (MapReadingGuardTests).
MAP_AUDIT_SHA256 = '957f955fd43f1b5a7f35d3c8e9d509a170a8f77f258c45cd25182d0d827e8645'

# Names under which compare.py holds symbol-map data: the parsed map and its entries, folds and
# thread-local entries, as locals or parameters, and as attributes of a Function.
MAP_NAMES = frozenset({'symbol_map', 'entries', 'tls_entries', 'folds'})
MAP_ATTRS = frozenset({'entries', 'tls_entries'})
# Every compare.py function that reads map data, audited against carry_forward_problem in the
# table in docs/comparator-contract.md ("Symbol map dependences"). From compare() only the
# statements that touch the map are fingerprinted, so its other checks can change freely.
MAP_READERS = ('load_symbol_map', 'check_tls', 'check_placement', 'Function.__init__', 'Function.resolve',
               'Function.secrel_field', 'Function.bind', 'Function.check_target_closure', 'compare')
PARTIAL_READERS = frozenset({'compare'})


def _strip_docstrings(tree):
    """Drop docstrings in place, so prose edits leave the fingerprint alone (comments never reach the AST)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) \
                and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:] or [ast.Pass()]
    return tree


def _touches_map(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in MAP_NAMES or isinstance(n, ast.arg) and n.arg in MAP_NAMES:
            return True
        if isinstance(n, ast.Attribute) and n.attr in MAP_ATTRS:
            return True
        # getattr(self, 'entries') and the like
        if isinstance(n, ast.Constant) and n.value in MAP_NAMES | MAP_ATTRS:
            return True
    return False


def _functions(tree):
    """Qualified name -> def node for module functions and class methods (nested defs stay inside)."""
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f'{node.name}.{item.name}'] = item
    return out


def _map_statements(stmts):
    """Statements that touch the map, descending into try blocks (which wrap most of compare())."""
    out = []
    for stmt in stmts:
        if isinstance(stmt, ast.Try):
            out += _map_statements(stmt.body)
            for handler in stmt.handlers:
                out += _map_statements(handler.body)
            out += _map_statements(stmt.orelse) + _map_statements(stmt.finalbody)
        elif _touches_map(stmt):
            out.append(stmt)
    return out


def map_audit(source):
    """(functions that touch map data, fingerprint of what they do with it) for comparator source.

    The fingerprint covers the audited functions (only the map statements of compare()), every
    compare.py function or Function method they call, transitively, and the module constants
    they name, as comment- and docstring-free AST dumps.
    """
    tree = _strip_docstrings(ast.parse(source))
    functions = _functions(tree)
    readers = {name for name, node in functions.items() if _touches_map(node)}
    readers |= {'<module>'} if any(_touches_map(n) for n in tree.body
                                   if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))) else set()
    constants = {t.id: n for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    parts, seen = [], set()
    queue = [(name, _map_statements(functions[name].body) if name in PARTIAL_READERS else [functions[name]])
             for name in MAP_READERS if name in functions]
    while queue:
        name, nodes = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        parts.append(name + '\n' + '\n'.join(ast.dump(n) for n in nodes))
        cls = name.split('.')[0] if '.' in name else None
        for n in (m for node in nodes for m in ast.walk(node)):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in functions:
                queue.append((n.func.id, [functions[n.func.id]]))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and f'{n.func.id}.__init__' in functions:
                queue.append((f'{n.func.id}.__init__', [functions[f'{n.func.id}.__init__']]))
            elif cls and isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self' \
                    and f'{cls}.{n.func.attr}' in functions:
                queue.append((f'{cls}.{n.func.attr}', [functions[f'{cls}.{n.func.attr}']]))
            elif isinstance(n, ast.Name) and n.id.isupper() and n.id in constants and n.id not in seen:
                queue.append((n.id, [constants[n.id]]))
    return readers, sha256('\n\n'.join(sorted(parts)).encode())


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


    def test_malformed_thread_local_entry_is_refused(self):
        for bad in ({'kind': 'thread-local', 'tls_offset': 8},
                    {'kind': 'thread-local', 'tls_offset': 8, 'size': None, 'rva': 8},
                    {'kind': 'thread-locals', 'tls_offset': 8, 'size': None},
                    {'kind': 'thread-local', 'tls_offset': -1, 'size': None},
                    {'kind': 'thread-local', 'tls_offset': True, 'size': None},
                    {'kind': 'thread-local', 'tls_offset': 8, 'size': 0},
                    {'kind': 'thread-local', 'tls_offset': '8', 'size': None}):
            with self.assertRaisesRegex(ValueError, 'must be {rva, size} or'):
                self.add({'tVar': bad}, allow_change=True)
        self.assertFalse((self.root / HISTORY).exists())

    def test_thread_local_entry_is_written_canonically(self):
        new = sm.plan(self.current_map(), self.incoming(
            {'tVar': {'size': 4, 'tls_offset': 8, 'kind': 'thread-local'}}))['map']
        self.assertEqual(list(new['symbols'])[-1], 'tVar')
        self.assertEqual(list(new['symbols']['tVar'].items()), [('kind', 'thread-local'), ('tls_offset', 8), ('size', 4)])

    def test_non_canonical_thread_local_entry_fails_the_map(self):
        smap = self.current_map()
        smap['symbols']['tVar'] = {'tls_offset': 8, 'kind': 'thread-local', 'size': None}
        with self.assertRaisesRegex(ValueError, 'in that order'):
            sm.check_map(smap)
        smap['symbols']['tVar'] = {'kind': 'thread-local', 'tls_offset': 8, 'size': None}
        sm.check_map(smap)

    def test_rva_entry_needs_exactly_rva_and_size(self):
        # The comparator ignores extra keys and a missing size, so each would give a second
        # spelling of one entry; the map allows one.
        for bad in ({'rva': FAR}, {'size': None, 'rva': FAR}, {'rva': FAR, 'size': None, 'tls_offset': 8},
                    {'rva': FAR, 'size': None, 'note': 'x'}):
            smap = self.current_map()
            smap['symbols']['Extra'] = bad
            with self.assertRaisesRegex(ValueError, 'exactly the keys rva, size'):
                sm.check_map(smap)
        smap['symbols']['Extra'] = {'rva': FAR, 'size': None}
        sm.check_map(smap)

    def test_incoming_rva_entry_is_written_canonically(self):
        new = sm.plan(self.current_map(), self.incoming({'A': {'rva': FAR}, 'B': {'size': 4, 'rva': FAR + 8}}))['map']
        self.assertEqual(list(new['symbols']['A'].items()), [('rva', FAR), ('size', None)])
        self.assertEqual(list(new['symbols']['B'].items()), [('rva', FAR + 8), ('size', 4)])

    def test_repository_maps_have_one_spelling_per_entry(self):
        maps = sorted((TOOLS.parent / 'reports').glob('*/symbol-map.json'))
        self.assertTrue(maps)
        for path in maps:
            sm.check_map(json.loads(path.read_text()), str(path))

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


class TlsAdditionTests(SymbolMapFixture, unittest.TestCase):
    """`_tls_index` and thread-local additions: the comparator checks both against the image's TLS
    directory for every function, so neither can be carried across (the fixture image has none)."""
    TLS = {'kind': 'thread-local', 'tls_offset': 8, 'size': 4}

    def comparator_result(self):
        report = self.run_comparator(obj=compiled_object(1))
        return report['result'], report['reason']

    def test_unrelated_addition_still_carries(self):
        self.add({'Unrelated': {'rva': FAR, 'size': None}})
        self.assertEqual(self.comparator_result(), ('pass', 'all-checks-passed'))
        self.check()

    def test_tls_index_addition_is_refused_and_lists_the_record(self):
        with self.assertRaisesRegex(ValueError, rf'adds _tls_index(.|\n)*stale: {RECORD}: _tls_index was added'):
            self.add({'_tls_index': {'rva': FAR, 'size': 4}})
        self.assertFalse((self.root / HISTORY).exists())

    def test_tls_index_addition_makes_record_stale(self):
        summary = self.add({'_tls_index': {'rva': FAR, 'size': 4}}, allow_change=True)
        self.assertEqual([p for p, _ in summary['stale_records']], [RECORD])
        # The rule's premise: the same record's runs would now fail.
        self.assertEqual(self.comparator_result(), ('fail', 'tls-directory-missing'))
        self.assertGateRejects('_tls_index was added')

    def test_tls_index_addition_is_refused_without_any_record(self):
        (self.root / RECORD).unlink()
        with self.assertRaisesRegex(ValueError, 'adds _tls_index'):
            self.add({'_tls_index': {'rva': FAR, 'size': 4}})

    def test_thread_local_addition_is_refused_and_lists_the_record(self):
        with self.assertRaisesRegex(ValueError, rf'stale: {RECORD}: thread-local entry tVar was added'):
            self.add({'tVar': self.TLS})
        self.assertFalse((self.root / HISTORY).exists())

    def test_thread_local_addition_makes_record_stale(self):
        self.add({'tVar': self.TLS}, allow_change=True)
        self.assertEqual(self.comparator_result(), ('fail', 'tls-directory-missing'))
        self.assertGateRejects('thread-local entry tVar was added')

    def test_thread_local_addition_without_records_is_accepted(self):
        (self.root / RECORD).unlink()
        self.add({'tVar': self.TLS})
        self.add({'Later': {'rva': FAR, 'size': None}})
        state = sm.load_state(self.root, MAP)
        self.assertEqual(len(state.valid), 3)

    def test_function_name_added_elsewhere_is_not_carried(self):
        reports = [run['report'] for run in self.record['runs']]
        state = sm.MapState({'symbols': {fx.FUNCTION: {'rva': FAR, 'size': None}}}, 'x' * 64, {}, set())
        self.assertIn('names the function', sm.carry_forward_problem(state, set(), fx.LAYOUT[fx.FUNCTION],
                                                                     len(fx.CODE), reports))


class ThreadLocalVersionTests(unittest.TestCase):
    """Changes to thread-local entries a record's version held, on a map whose records are stubs
    carrying only what the stale check reads (the synthetic image has no TLS directory, so no
    record pinned to a map with a thread-local entry can be produced by the comparator here)."""
    MAP = 'reports/b/symbol-map.json'
    RECORD = 'reports/b/0x1000.json'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        smap = {'schema': 1, 'build_id': 'b', 'folds': [], 'symbols': {
            'Fn': {'rva': 0x1000, 'size': 0x10},
            'tVar': {'kind': 'thread-local', 'tls_offset': 0x40, 'size': 8}}}
        path = self.root / self.MAP
        path.parent.mkdir(parents=True)
        path.write_bytes(sm.serialize(smap))
        record = {'symbol_map': {'path': self.MAP, 'sha256': sha256(path.read_bytes())},
                  'runs': [{'report': {'function': {'rva': 0x1000, 'size': 0x10, 'symbol': 'Fn'}, 'coverage': {}}}]}
        (self.root / self.RECORD).write_text(json.dumps(record))

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, symbols, **kw):
        return sm.apply_change(self.root, self.MAP, {'build_id': 'b', 'symbols': symbols}, **kw)

    def problem(self):
        sm._CACHE.clear()
        state = sm.load_state(self.root, self.MAP)
        return sm.record_problem(state, json.loads((self.root / self.RECORD).read_text()))

    def test_rva_addition_after_thread_local_entry_carries(self):
        # Same number as the thread-local offset: different address spaces, no shadowing.
        self.add({'Data': {'rva': 0x40, 'size': 8}})
        self.assertIsNone(self.problem())

    def test_changed_thread_local_entry_stales(self):
        moved = {'kind': 'thread-local', 'tls_offset': 0x48, 'size': 8}
        with self.assertRaisesRegex(ValueError, 'changes existing entries: tVar'):
            self.add({'tVar': moved})
        self.add({'tVar': moved}, allow_change=True)
        self.assertIn('changed or removed', self.problem())

    def test_resized_thread_local_entry_stales(self):
        self.add({'tVar': {'kind': 'thread-local', 'tls_offset': 0x40, 'size': None}}, allow_change=True)
        self.assertIn('changed or removed', self.problem())

    def test_removed_thread_local_entry_stales(self):
        with self.assertRaisesRegex(ValueError, 'removes entries: tVar'):
            sm.apply_change(self.root, self.MAP, {'build_id': 'b', 'symbols': {}}, remove=['tVar'])
        sm.apply_change(self.root, self.MAP, {'build_id': 'b', 'symbols': {}}, remove=['tVar'], allow_change=True)
        self.assertIn('changed or removed', self.problem())

    def test_second_thread_local_entry_stales(self):
        with self.assertRaisesRegex(ValueError, 'thread-local entry tOther was added'):
            self.add({'tOther': {'kind': 'thread-local', 'tls_offset': 0x80, 'size': 4}})
        self.add({'tOther': {'kind': 'thread-local', 'tls_offset': 0x80, 'size': 4}}, allow_change=True)
        self.assertIn('thread-local entry tOther', self.problem())

    def test_thread_local_entry_sharing_an_offset_is_refused(self):
        for entry in ({'kind': 'thread-local', 'tls_offset': 0x40, 'size': None},
                      {'kind': 'thread-local', 'tls_offset': 0x44, 'size': 4},
                      {'kind': 'thread-local', 'tls_offset': 0x3c, 'size': 8}):
            with self.assertRaisesRegex(ValueError, 'shares an address or range with existing entry tVar'):
                self.add({'tNew': entry})

    def test_unknown_entry_kind_is_not_carried(self):
        state = sm.MapState({'symbols': {'Odd': {'kind': 'other', 'rva': FAR}}}, 'x' * 64, {}, set())
        self.assertIn('no kind', sm.carry_forward_problem(state, set(), 0x1000, 0x10, [{}]))


class PresenceRuleCoverageTests(unittest.TestCase):
    """The comparator names special symbols and entry kinds only where carry_forward_problem has a rule."""
    COMPARE = TOOLS / 'compare.py'
    # Symbol-like string constants: leading underscore or MSVC decoration characters.
    SYMBOL_LIKE = re.compile(r'(_[A-Za-z_]\w*|\?[\w@?$]+)')

    def constants(self):
        """String constants of the comparator's two source files (pecoff.py holds the handler names)."""
        out = set()
        for path in (self.COMPARE, TOOLS / 'pecoff.py'):
            tree = ast.parse(path.read_text())
            out |= {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        return out

    def test_every_special_symbol_has_a_rule(self):
        names = {c for c in self.constants() if self.SYMBOL_LIKE.fullmatch(c)} - {'__main__'}
        self.assertTrue(names, 'the scan found no special symbol names in compare.py')
        self.assertLessEqual(names, sm.PRESENCE_NAMES,
                             'compare.py names a symbol carry_forward_problem has no rule for')
        self.assertLessEqual(set(EH_HANDLERS), sm.PRESENCE_NAMES)

    def test_every_entry_kind_has_a_rule(self):
        import compare
        self.assertEqual(sm.ENTRY_KINDS, {compare.THREAD_LOCAL})
        smap = {'schema': 1, 'build_id': 'b', 'symbols': {'X': {'kind': 'unheard-of', 'rva': 1}}}
        with self.assertRaisesRegex(Exception, 'unknown'):
            compare.load_symbol_map({'build_id': 'b'}, smap)

    def test_each_presence_name_is_not_carried(self):
        handlers = [{'coverage': {'eh': {'handlers': {'__CxxFrameHandler3': 1}}}}]
        for name in sorted(sm.PRESENCE_NAMES):
            state = sm.MapState({'symbols': {name: {'rva': FAR, 'size': None}}}, 'x' * 64, {}, set())
            self.assertIsNotNone(sm.carry_forward_problem(state, set(), 0x1000, 0x10, handlers), name)



class MapReadingGuardTests(unittest.TestCase):
    """compare.py reads the symbol map only where audited against carry_forward_problem.

    The audit is the "Symbol map dependences" table in docs/comparator-contract.md. A failure here
    means: re-audit that table and carry_forward_problem against the changed code, then update
    MAP_READERS or MAP_AUDIT_SHA256.
    """
    COMPARE = TOOLS / 'compare.py'

    def guard_problem(self, source):
        readers, digest = map_audit(source)
        if readers != set(MAP_READERS):
            return f'map data is read outside the audited functions: {sorted(readers ^ set(MAP_READERS))}'
        if digest != MAP_AUDIT_SHA256:
            return 'an audited function changed what it does with the symbol map'
        return None

    def test_comparator_reads_the_map_only_as_audited(self):
        problem = self.guard_problem(self.COMPARE.read_text())
        self.assertIsNone(problem, f'{problem}: re-audit carry_forward_problem in tools/symbol_map.py and the '
                                   'table in docs/comparator-contract.md, then update this test')

    def mutated(self, old, new, source=None):
        source = self.COMPARE.read_text() if source is None else source
        self.assertEqual(source.count(old), 1, old)
        return source.replace(old, new)

    # Each mutation would let a re-run reject a map addition that carry_forward_problem carries
    # across (or change which ones it rejects), so the guard must see it.
    MUTATIONS = {
        'function overlap widened': (
            'overlaps = start < rva < end or (size is not None and rva < end and start < rva + size)',
            'overlaps = start - 16 < rva < end or (size is not None and rva < end and start < rva + size)'),
        'funclet overlap widened': ("need(not (rva <= entry['rva'] < end or",
                                    "need(not (rva - 16 <= entry['rva'] < end or"),
        'tls template bound tightened': ("need(entry['tls_offset'] + (entry.get('size') or 1) <= end - start,",
                                         "need(entry['tls_offset'] + (entry.get('size') or 1) <= end - start - 8,"),
        'closure handler test dropped': ("self.target_u32(current + length, 'target handler') in funcinfo_handlers:",
                                         'True:'),
        'new method reads the entries': ('    def target_u32(self, rva, what):',
                                         '    def big(self):\n        return [n for n in self.entries if n]\n\n'
                                         '    def target_u32(self, rva, what):'),
        'map read through getattr': ('    def target_u32(self, rva, what):',
                                     "    def big(self):\n        return getattr(self, 'tls_entries')\n\n"
                                     '    def target_u32(self, rva, what):'),
        'called helper changed': ('def is_uint(value):\n', 'def is_uint(value):\n    value = abs(value)\n'),
        'constant changed': ("TLS_INDEX = '_tls_index'", "TLS_INDEX = '_tls_index_'"),
    }

    def test_mutations_of_map_reading_code_are_caught(self):
        for label, (old, new) in self.MUTATIONS.items():
            with self.subTest(label):
                self.assertIsNotNone(self.guard_problem(self.mutated(old, new)))

    def test_comment_and_docstring_edits_pass(self):
        source = self.mutated(
            '# placement, alias, fold and overlap checks and every non-SECREL reference see RVA entries only.',
            '# placement, alias, fold and overlap checks and all non-SECREL references see RVA entries only.')
        source = self.mutated("for name, entry in self.entries.items():\n",
                              "for name, entry in self.entries.items():  # every entry, not only referenced\n", source)
        source = self.mutated('"""Validate thread-local entries and any `_tls_index` entry against',
                              '"""Check thread-local entries and any `_tls_index` entry against', source)
        self.assertIsNone(self.guard_problem(source))

    def test_edits_outside_map_reading_pass(self):
        # Checks that never see the map may change without a re-audit.
        source = self.mutated("need(not unused, 'eh-data-unaccounted',", "need(not unused and True, 'eh-data-unaccounted',")
        self.assertIsNone(self.guard_problem(source))


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

    def test_two_ascending_disjoint_funclets_carry(self):
        ranges = [[0x2000, 0x20], [0x2020, 0x10]]
        self.assertIsNone(self.problem({'Far': {'rva': FAR, 'size': 8}}, self.reports(ranges, sections=2, total=0x30)))

    def test_funclets_in_binding_order_carry(self):
        # The comparator lists funclets in the order it bound them, which need not be by address.
        ranges = [[0x2020, 0x10], [0x2000, 0x20]]
        self.assertIsNone(self.problem({'Far': {'rva': FAR, 'size': 8}}, self.reports(ranges, sections=2, total=0x30)))
        self.assertIn('funclet range', self.problem({'In': {'rva': 0x2028, 'size': None}},
                                                    self.reports(ranges, sections=2, total=0x30)))
        self.assertEqual(sm.funclet_ranges([r['coverage'] for r in self.reports(ranges, sections=2, total=0x30)],
                                           self.RVA, self.SIZE), [(0x2000, 0x20), (0x2020, 0x10)])

    def test_runs_listing_funclets_in_another_order_refused(self):
        # Runs of one compile bind in one order, so a reordering is a disagreement, not a match.
        reports = self.reports([[0x2000, 0x20], [0x2020, 0x10]], sections=2, total=0x30)
        reports[1]['coverage']['funclet_ranges'] = [[0x2020, 0x10], [0x2000, 0x20]]
        self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}}, reports))

    def test_overlapping_funclets_refused_in_any_order(self):
        for ranges in ([[0x2000, 0x20], [0x2010, 0x10]], [[0x2010, 0x10], [0x2000, 0x20]],
                       [[0x2000, 0x20], [0x2000, 0x10]], [[0x2000, 0x10], [0x2000, 0x20]]):
            self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}},
                                                      self.reports(ranges, sections=2, total=0x30)), ranges)

    def test_funclet_overlapping_the_function_refused(self):
        for start, length in ((self.RVA, 0x20), (self.RVA + 0x30, 0x20), (self.RVA - 0x10, 0x20)):
            self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}},
                                                      self.reports([[start, length]], total=length)))

    def test_funclet_adjacent_to_the_function_carries(self):
        self.assertIsNone(self.problem({'Far': {'rva': FAR, 'size': 8}},
                                       self.reports([[self.RVA + self.SIZE, 0x20]])))

    def test_non_integer_counts_refused(self):
        for key, value in (('funclet_sections', 1.0), ('funclet_sections', True), ('funclet_bytes_total', 32.0)):
            reports = self.reports([list(self.FUNCLET)])
            for r in reports:
                r['coverage'][key] = value
            self.assertIn('do not give', self.problem({'Far': {'rva': FAR, 'size': 8}}, reports), key)


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
