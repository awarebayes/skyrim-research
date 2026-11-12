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


if __name__ == '__main__':
    unittest.main()
