"""tools/verifier/bind.py on the original synthetic object and image (no game data, no demangler needed)."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bind  # noqa: E402
from compare import compare  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402


class BindTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.task_dir = self.root / 'task'
        self.task_dir.mkdir()
        (self.root / 'obj').write_bytes(fx.coff_object())
        (self.root / 'image').write_bytes(fx.pe_image())
        pack = self.root / 'packs' / 'p'
        pack.mkdir(parents=True)
        # The pack lists the targets the analysis saw; names differ from the stand-ins on purpose.
        refs = [{'target_rva': fx.LAYOUT[fx.CALLEE], 'community_names': [{'name': 'RE::Other::AddOne', 'kind': 'func'}]},
                {'target_rva': fx.LAYOUT[fx.BASE], 'community_names': []}]
        (pack / 'pack.json').write_text(json.dumps({'references': refs}))
        self.write_task('unbound:Synthetic::SyntheticSum', {})

    def tearDown(self):
        self.tmp.cleanup()

    def write_task(self, symbol, symbols, hints=None):
        task = {'symbols': 'symbols.json', 'functions': [
            {'rva': hex(fx.LAYOUT[fx.FUNCTION]), 'size': len(fx.CODE), 'symbol': symbol,
             'community_name': 'Synthetic::SyntheticSum', 'pack': 'packs/p'}]}
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        (self.task_dir / 'symbols.json').write_text(json.dumps({'schema': 1, 'symbols': symbols}))
        if hints is not None:
            (self.task_dir / bind.HINTS).write_text(json.dumps(hints))

    def run_bind(self):
        report = bind.bind(self.task_dir, self.root / 'obj', self.root / 'image', repo=self.root)
        return report, json.loads((self.task_dir / 'symbols.json').read_text())['symbols']

    def test_function_by_member_name_and_references_by_position(self):
        report, symbols = self.run_bind()
        self.assertEqual(report['functions'][0]['how'], 'member name')
        self.assertEqual(symbols[fx.FUNCTION], {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)})
        self.assertEqual(symbols[fx.CALLEE]['rva'], fx.LAYOUT[fx.CALLEE])
        self.assertEqual(symbols[fx.BASE]['rva'], fx.LAYOUT[fx.BASE])
        # Not listed in the pack, so position alone does not bind it.
        self.assertEqual(report['unbound_references'], [fx.COUNTER])
        text = '\n'.join(bind.describe(report, self.task_dir))
        self.assertIn(f'UNBOUND reference {fx.COUNTER}', text)
        self.assertIn(bind.HINTS, text)

    def test_hint_binds_unlisted_reference(self):
        self.write_task('unbound:x', {}, hints={fx.COUNTER: hex(fx.LAYOUT[fx.COUNTER])})
        report, symbols = self.run_bind()
        self.assertEqual(report['unbound_references'], [])
        self.assertEqual(symbols[fx.COUNTER]['rva'], fx.LAYOUT[fx.COUNTER])

    def test_hint_replaces_a_stale_reference_entry(self):
        # A misaligned earlier attempt can leave another listed target in the map.
        self.write_task('unbound:x', {fx.COUNTER: {'rva': fx.LAYOUT[fx.BASE], 'size': None}},
                        hints={fx.COUNTER: hex(fx.LAYOUT[fx.COUNTER])})
        report, symbols = self.run_bind()
        self.assertEqual(symbols[fx.COUNTER]['rva'], fx.LAYOUT[fx.COUNTER])
        how = {r['symbol']: r['how'] for r in report['references']}[fx.COUNTER]
        self.assertEqual(how, f'hint, replaced {hex(fx.LAYOUT[fx.BASE])}')

    def test_renamed_function_is_reported_and_old_entry_dropped(self):
        old = '?SyntheticSum@Synthetic@@QEAAHXZ'
        self.write_task(old, {old: {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)}})
        report, symbols = self.run_bind()
        self.assertEqual(report['renamed'], [{'rva': hex(fx.LAYOUT[fx.FUNCTION]), 'old': old, 'new': fx.FUNCTION}])
        self.assertNotIn(old, symbols)
        self.assertIn('decorated name changed', '\n'.join(bind.describe(report, self.task_dir)))

    def test_function_hint_by_rva(self):
        task = json.loads((self.task_dir / 'task.json').read_text())
        task['functions'][0]['community_name'] = 'Unrelated::Name'
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        report, _ = self.run_bind()
        self.assertEqual(report['functions'], [])
        self.assertIn(fx.FUNCTION, report['unbound_functions'][0]['defined_in_object'])
        (self.task_dir / bind.HINTS).write_text(json.dumps({fx.FUNCTION: hex(fx.LAYOUT[fx.FUNCTION])}))
        report, _ = self.run_bind()
        self.assertEqual(report['functions'][0]['how'], 'hint')

    def test_misaligned_position_does_not_bind_an_unknown_address(self):
        (self.root / 'image').write_bytes(fx.pe_image(link_addresses={fx.CALLEE: 0x1008}))
        report, symbols = self.run_bind()
        # 0x1008 is not a listed reference, so the call falls back to the name rule and stays unbound.
        self.assertIn(fx.CALLEE, report['unbound_references'])

    def test_qualified_names(self):
        self.assertEqual(bind.qualified('public: static struct H<class A> __cdecl M<class A, struct B>::Get(class A *)'),
                         'M::Get')
        self.assertEqual(bind.qualified('public: static float BSTimer::Q'), 'BSTimer::Q')
        self.assertEqual(bind.fallback_qualified('?Visit@Base@@UEAAIPEAX@Z'), 'Base::Visit')
        self.assertEqual(bind.community_qualified('RE::BSPointerHandleManagerInterface<Actor>::GetHandle'),
                         'BSPointerHandleManagerInterface::GetHandle')


# Listings in the pack format, written by hand for these tests (no tool or game output).
SCALAR_LISTING = """Function FUN_1 at rva 0x1000
  +0x000  PUSH RBX
  +0x002  SUB RSP,0x20
  +0x006  MOV EBX,EDX                                     
  +0x008  CALL 0x140002000                                 [UNCONDITIONAL_CALL 0x2000 FUN_2]
  +0x00d  TEST BL,0x1
  +0x010  JZ 0x14000101c
  +0x012  MOV EDX,0x18
  +0x017  CALL 0x140003000                                 [UNCONDITIONAL_CALL 0x3000 FUN_3]
  +0x01c  RET
"""
VECTOR_LISTING = """  +0x000  TEST DL,0x2
  +0x003  JZ 0x140001010
  +0x005  CALL 0x140003000
  +0x00a  RET
"""
CLOBBERED_LISTING = """  +0x000  MOV EDX,0x8
  +0x005  TEST DL,0x1
  +0x008  RET
"""
CALL_CLOBBERS_LISTING = """  +0x000  CALL 0x140002000
  +0x005  TEST DL,0x1
  +0x008  JZ 0x140001010
  +0x00a  CALL 0x140003000
"""
PLAIN = '??1Synth@@UEAA@XZ'
SCALAR = '??_GSynth@@UEAAPEAXI@Z'
VECTOR = '??_ESynth@@UEAAPEAXI@Z'
THUNK = '??_ESynth@@WBA@EAAPEAXI@Z'


class DestructorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.task_dir = self.root / 'task'
        self.task_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def setup_task(self, defined, listing=SCALAR_LISTING, name_how='slot 0', symbol='unbound:Synth::~Synth',
                   size=29, hints=None):
        unit = fx.Unit()
        for name, length in defined.items():
            sec = unit.section('.text$mn', b'\xc3' * length, fx.SCN_CODE)
            unit.define(name, sec, storage=fx.STORAGE_EXTERNAL, function=True)
        (self.root / 'obj').write_bytes(unit.coff())
        pack = self.root / 'packs' / 'd'
        pack.mkdir(parents=True, exist_ok=True)
        (pack / 'pack.json').write_text(json.dumps({'identity': {'name_how': name_how}, 'references': []}))
        if listing is not None:
            (pack / 'listing.txt').write_text(listing)
        task = {'symbols': 'symbols.json', 'functions': [
            {'rva': '0x1000', 'size': size, 'symbol': symbol, 'community_name': 'RE::Synth::~Synth', 'pack': 'packs/d'}]}
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        smap = {symbol: {'rva': 0x1000, 'size': size}} if not symbol.startswith('unbound:') else {}
        (self.task_dir / 'symbols.json').write_text(json.dumps({'schema': 1, 'symbols': smap}))
        if hints is not None:
            (self.task_dir / bind.HINTS).write_text(json.dumps(hints))

    def run_bind(self):
        report = bind.bind(self.task_dir, self.root / 'obj', None, repo=self.root)
        task = json.loads((self.task_dir / 'task.json').read_text())
        return report, task['functions'][0]

    def test_spec_from_listing(self):
        spec = bind.destructor_spec('Synth::~Synth', 'slot 0', SCALAR_LISTING)
        self.assertEqual((spec['symbols'], spec['decided']), (['??_G'], True))
        self.assertEqual(bind.destructor_spec('Synth::~Synth', 'slot 0', VECTOR_LISTING)['symbols'], ['??_E'])
        # The flag register overwritten, or clobbered by a call, is no flag test.
        self.assertEqual(bind.destructor_spec('Synth::~Synth', 'name', CLOBBERED_LISTING)['symbols'], ['??1'])
        self.assertEqual(bind.destructor_spec('Synth::~Synth', 'name', CALL_CLOBBERS_LISTING)['symbols'], ['??1'])
        undecided = bind.destructor_spec('Synth::~Synth', 'slot 0', None)
        self.assertEqual((sorted(undecided['symbols']), undecided['decided']), (['??1', '??_E', '??_G'], False))
        self.assertIsNone(bind.destructor_spec('Synth::Update', 'slot 3', SCALAR_LISTING))
        self.assertIsNone(bind.destructor_spec('Synth::Dtor', 'table', SCALAR_LISTING))

    def test_decoration(self):
        self.assertEqual(bind.dtor_decoration(SCALAR), ('??_G', 'Synth'))
        self.assertEqual(bind.dtor_decoration('??_GInner@Outer@@UEAAPEAXI@Z'), ('??_G', 'Outer::Inner'))
        self.assertIsNone(bind.dtor_decoration(THUNK))
        self.assertIsNone(bind.dtor_decoration('?Update@Synth@@UEAAXXZ'))

    def test_plain_destructor_rebound_to_scalar_deleting(self):
        self.setup_task({PLAIN: 12, SCALAR: 29, THUNK: 9}, symbol=PLAIN)
        report, fn = self.run_bind()
        self.assertEqual(fn['symbol'], SCALAR)
        self.assertEqual(fn['destructor']['symbols'], ['??_G'])
        self.assertEqual(report['renamed'], [{'rva': '0x1000', 'old': PLAIN, 'new': SCALAR}])
        symbols = json.loads((self.task_dir / 'symbols.json').read_text())['symbols']
        self.assertNotIn(PLAIN, symbols)

    def test_unbound_names_the_expected_kind(self):
        self.setup_task({PLAIN: 12})
        report, fn = self.run_bind()
        self.assertEqual(report['functions'], [])
        self.assertEqual(report['unbound_functions'][0]['expected']['symbols'], ['??_G'])
        text = '\n'.join(bind.describe(report, self.task_dir))
        self.assertIn('scalar deleting destructor', text)
        self.assertIn('constructor', text)

    def test_undecided_binds_by_size_and_reports_choice(self):
        self.setup_task({PLAIN: 12, SCALAR: 29, VECTOR: 40}, listing=None)
        report, fn = self.run_bind()
        self.assertEqual(fn['symbol'], SCALAR)
        self.assertEqual(report['functions'][0]['how'], 'destructor kind, size match')
        choice = report['destructor_choices'][0]
        self.assertEqual([c['symbol'] for c in choice['candidates']], [SCALAR, VECTOR, PLAIN])
        self.assertIn(f'bound to {SCALAR}', '\n'.join(bind.describe(report, self.task_dir)))

    def test_unused_hint_is_reported(self):
        self.setup_task({PLAIN: 12}, listing=CLOBBERED_LISTING, name_how='name', hints={SCALAR: '0x1000'})
        report, fn = self.run_bind()
        self.assertEqual(fn['symbol'], PLAIN)
        self.assertEqual(report['ignored_hints'][0]['hint'], SCALAR)
        self.assertIn('not defined in the compiled object', report['ignored_hints'][0]['reason'])
        self.assertIn(f'WARNING bind hint {SCALAR}', '\n'.join(bind.describe(report, self.task_dir)))

    def test_hint_overriding_evidence_is_used_and_warned(self):
        self.setup_task({PLAIN: 12, SCALAR: 29}, hints={PLAIN: '0x1000'})
        report, fn = self.run_bind()
        self.assertEqual(fn['symbol'], PLAIN)
        self.assertEqual(report['ignored_hints'], [])
        self.assertIn('overrides the pack evidence', report['warnings'][0])


DTOR = 'SyntheticDtor'
DTOR_RVA = fx.LAYOUT[fx.OTHER_CALLEE]


class FuncletTests(unittest.TestCase):
    """References made only from funclets, on the synthetic catch unit (catch$0 and dtor$0)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.task_dir = self.root / 'task'
        self.task_dir.mkdir()
        unit = fx.catch_unit()
        # The unwind funclet calls a destructor nothing else in the unit references.
        x = next(i for i, sec in enumerate(unit.sections, 1) if sec[0] == '.text$x')
        unit.sections[x - 1][2] = [(o, DTOR if o == 0x29 else sym, k) for o, sym, k in unit.sections[x - 1][2]]
        unit.external(DTOR)
        self.unit = unit
        self.externals = fx.image_externals(**{DTOR: DTOR_RVA})
        self.image = unit.link(self.externals)
        (self.root / 'obj').write_bytes(unit.coff())
        (self.root / 'image').write_bytes(self.image)
        self.dtor_rva = fx.section_rva(unit, '?dtor$0@?0??SyntheticCatch@@4HA')

    def tearDown(self):
        self.tmp.cleanup()

    def setup_task(self, calls, hints=None, funclet=True):
        pack = self.root / 'packs' / 'c'
        pack.mkdir(parents=True, exist_ok=True)
        states = [{'state': 0, 'to_state': -1, 'funclet': self.dtor_rva if funclet else None, 'calls': calls}]
        (pack / 'pack.json').write_text(json.dumps({
            'references': [{'target_rva': fx.LAYOUT[fx.CALLEE], 'community_names': []}],
            'object_lifetimes': {'states': states, 'try_blocks': []}}))
        rva = fx.section_rva(self.unit, fx.CATCH_FUNCTION)
        task = {'symbols': 'symbols.json', 'functions': [
            {'rva': hex(rva), 'size': len(fx.CATCH_CODE), 'symbol': fx.CATCH_FUNCTION,
             'community_name': 'SyntheticCatch', 'pack': 'packs/c'}]}
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        (self.task_dir / 'symbols.json').write_text(json.dumps({'schema': 1, 'symbols': {}}))
        if hints is not None:
            (self.task_dir / bind.HINTS).write_text(json.dumps(hints))

    def run_bind(self, image=True):
        report = bind.bind(self.task_dir, self.root / 'obj', self.root / 'image' if image else None, repo=self.root)
        return report, json.loads((self.task_dir / 'symbols.json').read_text())['symbols']

    def test_funclets_found_with_unwind_state(self):
        obj = bind.CoffObject(self.unit.coff())
        defined = bind.defined_functions(obj)
        found = bind.funclets(obj, defined[fx.CATCH_FUNCTION], set(defined.values()))
        x = next(i for i, sec in enumerate(self.unit.sections, 1) if sec[0] == '.text$x')
        self.assertEqual(found, {x: (0, 0x21)})

    def test_lifetime_callee_bound_by_funclet_position(self):
        self.setup_task([hex(DTOR_RVA)], hints={fx.BASE: hex(self.externals[fx.BASE])})
        report, symbols = self.run_bind()
        self.assertEqual(report['unbound_references'], [])
        got = {r['symbol']: r for r in report['references']}
        self.assertEqual((got[DTOR]['how'], got[DTOR]['from']), ('object lifetime position', 'funclet'))
        self.assertEqual(symbols[DTOR]['rva'], DTOR_RVA)
        # The catch funclet's global is bound only because funclets are scanned at all.
        self.assertEqual((got[fx.BASE]['how'], got[fx.BASE]['from']), ('hint', 'funclet'))
        self.assertEqual(got[fx.CALLEE]['how'], 'position')
        # The comparator, which compares funclets too, passes with exactly this map.
        smap = dict(symbols, **{n: {'rva': r, 'size': None} for n, r in fx.HANDLER_THUNKS.items()},
                    **fx.catch_map(self.unit))
        args = fx.unit_inputs(self.unit, fx.CATCH_FUNCTION, self.externals, image=self.image)
        args['symbol_map']['symbols'] = smap
        result = compare(**args)
        self.assertEqual(result['result'], 'pass', result.get('detail'))
        self.assertGreater(result['coverage']['funclet_sections'], 0)

    def test_without_position_single_lifetime_call_binds(self):
        self.setup_task([hex(DTOR_RVA) + ' Synthetic::~Synthetic'], hints={fx.BASE: '0x3100'}, funclet=False)
        report, symbols = self.run_bind(image=False)
        self.assertEqual(symbols[DTOR]['rva'], DTOR_RVA)
        self.assertEqual({r['symbol']: r['how'] for r in report['references']}[DTOR], 'object lifetime')

    def test_position_contradicting_the_lifetime_call_does_not_bind(self):
        self.setup_task(['0x1004'], hints={fx.BASE: '0x3100'})
        report, symbols = self.run_bind()
        self.assertNotIn(DTOR, symbols)
        self.assertEqual(report['unbound_references'], [DTOR])

    def test_funclet_only_reference_without_hint_is_listed(self):
        self.setup_task([hex(DTOR_RVA)])
        report, symbols = self.run_bind()
        self.assertIn(fx.BASE, report['unbound_references'])
        self.assertIn(f'UNBOUND reference {fx.BASE}', '\n'.join(bind.describe(report, self.task_dir)))

    def test_lifetime_name_binds_by_community_name(self):
        # Two calls in the state, so only the community name can pick one.
        self.setup_task(['0x1000 RE::Other', hex(DTOR_RVA) + ' RE::SyntheticDtor'], hints={fx.BASE: '0x3100'},
                        funclet=False)
        report, symbols = self.run_bind(image=False)
        self.assertEqual(symbols[DTOR]['rva'], DTOR_RVA)
        self.assertEqual({r['symbol']: r['how'] for r in report['references']}[DTOR], 'community name')


class PublicMapBindTests(BindTests):
    """A task naming the repository map: bind adds through tools/symbol_map.py, never by hand."""
    MAP = 'reports/synthetic-fixture/symbol-map.json'

    def write_task(self, symbol, symbols, hints=None):
        super().write_task(symbol, symbols, hints)
        task = json.loads((self.task_dir / 'task.json').read_text())
        task['symbols'] = self.MAP
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        path = self.root / self.MAP
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema': 1, 'build_id': 'synthetic-fixture', 'symbols': symbols,
                                    'folds': []}, indent=2) + '\n')

    def run_bind(self):
        report = bind.bind(self.task_dir, self.root / 'obj', self.root / 'image', repo=self.root)
        return report, json.loads((self.root / self.MAP).read_text())['symbols']

    def test_additions_go_through_the_history(self):
        self.run_bind()
        history = json.loads((self.root / 'reports/synthetic-fixture/symbol-map.history.json').read_text())
        self.assertEqual(len(history['versions']), 2)
        self.assertIn(fx.FUNCTION, history['versions'][1]['added'])

    def test_rename_that_would_stale_a_record_is_refused(self):
        old = '?SyntheticSum@Synthetic@@QEAAHXZ'
        self.write_task(old, {old: {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)}})
        blob = (self.root / self.MAP).read_bytes()
        record = {'symbol_map': {'path': self.MAP, 'sha256': hashlib.sha256(blob).hexdigest()},
                  'runs': [{'report': {'function': {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)},
                                       'coverage': {}}}]}
        (self.root / 'reports/synthetic-fixture/0x1010.json').write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.run_bind()
        self.assertEqual((self.root / self.MAP).read_bytes(), blob)


class ThreadLocalBindTests(unittest.TestCase):
    """A SECREL reference binds only through a `tls:` hint, as a thread-local entry; _tls_index never."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.task_dir = self.root / 'task'
        self.task_dir.mkdir()
        unit = fx.tls_unit()
        (self.root / 'obj').write_bytes(unit.coff())
        image = unit.link({fx.TLS_INDEX: fx.TLS_INDEX_RVA}, tls=fx.tls_layout())
        (self.root / 'image').write_bytes(image)
        rva = unit.default_placement()[1]
        pack = self.root / 'packs' / 't'
        pack.mkdir(parents=True)
        # Even a pack listing the very value the target's SECREL field holds must not bind it as an RVA.
        refs = [{'target_rva': fx.TLS_OFFSET, 'community_names': [{'name': 'tSyntheticGuard', 'kind': 'data'}]},
                {'target_rva': fx.TLS_INDEX_RVA, 'community_names': []}]
        (pack / 'pack.json').write_text(json.dumps({'references': refs}))
        task = {'symbols': 'symbols.json', 'functions': [
            {'rva': hex(rva), 'size': len(fx.TLS_CODE), 'symbol': fx.TLS_FUNCTION,
             'community_name': 'SyntheticTlsRead', 'pack': 'packs/t'}]}
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        (self.task_dir / 'symbols.json').write_text(json.dumps(
            {'schema': 1, 'symbols': {fx.TLS_FUNCTION: {'rva': rva, 'size': len(fx.TLS_CODE)}}}))

    def tearDown(self):
        self.tmp.cleanup()

    def run_bind(self, hints=None):
        if hints is not None:
            (self.task_dir / bind.HINTS).write_text(json.dumps(hints))
        report = bind.bind(self.task_dir, self.root / 'obj', self.root / 'image', repo=self.root)
        return report, json.loads((self.task_dir / 'symbols.json').read_text())['symbols']

    def test_unhinted_thread_local_stays_unbound(self):
        report, symbols = self.run_bind()
        self.assertEqual(report['unbound_thread_locals'], [fx.TLS_VAR])
        self.assertEqual(report['unbound_references'], [])
        self.assertNotIn(fx.TLS_VAR, symbols)
        self.assertNotIn(fx.TLS_INDEX, symbols)
        self.assertIn('tls:0x<offset>', '\n'.join(bind.describe(report, self.task_dir)))

    def test_tls_hint_writes_thread_local_entry(self):
        report, symbols = self.run_bind({fx.TLS_VAR: hex(fx.TLS_OFFSET).replace('0x', 'tls:0x')})
        self.assertEqual(report['unbound_thread_locals'], [])
        self.assertEqual(symbols[fx.TLS_VAR], {'kind': 'thread-local', 'tls_offset': fx.TLS_OFFSET, 'size': None})
        self.assertNotIn(fx.TLS_INDEX, symbols)
        self.assertIn('thread-local hint', '\n'.join(bind.describe(report, self.task_dir)))

    def test_malformed_tls_hint_rejected(self):
        with self.assertRaises(ValueError):
            self.run_bind({fx.TLS_VAR: 'tls:seven'})

    def test_unused_tls_hint_is_listed_as_ignored(self):
        hint = '?tUnused@@3HA'
        report, symbols = self.run_bind({fx.TLS_VAR: hex(fx.TLS_OFFSET).replace('0x', 'tls:0x'), hint: 'tls:0x40'})
        self.assertEqual([h['hint'] for h in report['ignored_hints']], [hint])
        self.assertNotIn(hint, symbols)
        self.assertIn(f'bind hint {hint} -> tls:0x40 ignored', '\n'.join(bind.describe(report, self.task_dir)))

    def test_used_tls_hint_stays_used_once_bound(self):
        hints = {fx.TLS_VAR: hex(fx.TLS_OFFSET).replace('0x', 'tls:0x')}
        self.run_bind(hints)
        report, _ = self.run_bind(hints)
        self.assertEqual(report['ignored_hints'], [])

    def test_thread_local_is_not_published_to_the_repository_map(self):
        name = 'reports/synthetic-fixture/symbol-map.json'
        task = json.loads((self.task_dir / 'task.json').read_text())
        task['symbols'] = name
        (self.task_dir / 'task.json').write_text(json.dumps(task))
        smap = json.loads((self.task_dir / 'symbols.json').read_text())
        smap.update(build_id='synthetic-fixture', folds=[])
        path = self.root / name
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(smap, indent=2) + '\n')
        blob = path.read_bytes()
        (self.task_dir / bind.HINTS).write_text(json.dumps({fx.TLS_VAR: hex(fx.TLS_OFFSET).replace('0x', 'tls:0x')}))
        with self.assertRaisesRegex(ValueError, 'thread-local'):
            bind.bind(self.task_dir, self.root / 'obj', self.root / 'image', repo=self.root)
        self.assertEqual(path.read_bytes(), blob)


if __name__ == '__main__':
    unittest.main()
