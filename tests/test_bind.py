"""tools/verifier/bind.py on the original synthetic object and image (no game data, no demangler needed)."""
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


if __name__ == '__main__':
    unittest.main()
