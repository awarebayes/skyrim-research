"""tools/build_fnv_index.py and the pack's "Sibling source" section, on an original synthetic
sibling tree and synthetic analysis tables (no game or FNV material)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'ghidra'))
import build_fnv_index as fi  # noqa: E402
import export_pack as ep  # noqa: E402

HEADERS = {
    'Base.h': 'class Base\n{\npublic:\n    virtual ~Base();\n    virtual void Tick();\n    virtual int Count() const;\n};\n',
    'Widget.h': 'class Widget : public Base\n{\npublic:\n    virtual ~Widget();\n    virtual int Count() const;\n'
                '    virtual void Draw(int a);\n    int GetFlags() const { return flags; }\n    int flags;\n};\n',
    'Orphan.h': 'class Orphan : public Missing\n{\n    virtual void Run();\n};\n',
}
SOURCE = ('#include "Widget.h"\n\nWidget::~Widget()\n{\n}\n\nint Widget::Count() const\n{\n    return 0;\n}\n\n'
          'void Widget::Draw(int a)\n{\n}\n\nvoid FUN_00401000_shell::Poke()\n{\n}\n\nstatic int FreeHelper(int x)\n{\n'
          '    return x;\n}\n')
UNITS = {'units': [
    {'source': 'src/core/widget.cpp', 'compiler': 'sp1', 'flags': ['/MT', '/O2', '/GS'], 'functions': [
        {'symbol': '??1Widget@@UAE@XZ', 'address': '0x00401000', 'size': 12},
        {'symbol': '??_GWidget@@UAEPAXI@Z', 'address': '0x00401010', 'size': 30},
        {'symbol': '?Count@Widget@@UBEHXZ', 'address': '0x00401040', 'size': 3},
        {'symbol': '?Draw@Widget@@UAEXH@Z', 'address': '0x00401050', 'size': 80},
        {'symbol': '?GetFlags@Widget@@QBEHXZ', 'address': '0x00401100', 'size': 4},
        {'symbol': '?Poke@FUN_00401000_shell@@QAEXXZ', 'address': '0x00401110', 'size': 9},
        {'symbol': '?FreeHelper@@YAHH@Z', 'address': '0x00401120', 'size': 5}]},
    {'source': 'src/game/other.cpp', 'compiler': 'rtm', 'flags': ['/Od', '/Oy-'], 'functions': [
        {'symbol': '?vf12@Widget@@UAEXXZ', 'address': '0x00402000', 'size': 20}]},
]}


def fn(rva, names, owner=None, slot=None):
    return {'rva': rva, 'size': 16, 'names': names,
            'owner': {'class': owner, 'how': 'vtable', 'slot': slot} if owner else None}


class FnvIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.fnv = base / 'fnv'
        (self.fnv / 'include').mkdir(parents=True)
        (self.fnv / 'build').mkdir()
        (self.fnv / 'src/core').mkdir(parents=True)
        for name, text in HEADERS.items():
            (self.fnv / 'include' / name).write_text(text)
        (self.fnv / 'src/core/widget.cpp').write_text(SOURCE)
        (self.fnv / 'build/units.json').write_text(json.dumps(UNITS))
        self.analysis = base / 'analysis'
        self.analysis.mkdir()
        # Our Widget: slot 0 deleting dtor, 1 Tick (inherited), 2 Count (named), 3 an unnamed own override.
        functions = [
            fn(0x100, [{'name': 'Widget::~Widget', 'source': 'ng-slot', 'how': 'slot 0'}], 'Widget', 0),
            fn(0x200, [{'name': 'Base::Tick', 'source': 'ng-slot', 'how': 'slot 1'}], 'Base', 1),
            fn(0x300, [{'name': 'Widget::Count', 'source': 'ng-slot', 'how': 'slot 2'}], 'Widget', 2),
            fn(0x400, [], 'Widget', 3),
            fn(0x500, [{'name': 'Widget::sub', 'source': 'meh321', 'how': 'placeholder'}], 'Widget'),
        ]
        with open(self.analysis / 'functions.jsonl', 'w') as fh:
            for r in functions:
                fh.write(json.dumps(r) + '\n')
        classes = [{'class': 'Widget', 'slots': [0x100, 0x200, 0x300, 0x400],
                    'slot_names': {'0': {'name': '~Widget', 'declared_in': 'Widget'},
                                   '2': {'name': 'Count', 'declared_in': 'Base'}}}]
        with open(self.analysis / 'classes.jsonl', 'w') as fh:
            for c in classes:
                fh.write(json.dumps(c) + '\n')

    def tearDown(self):
        self.tmp.cleanup()
        ep._sibling.clear()

    def by_symbol(self):
        records, counts = fi.build(self.fnv, self.analysis)
        return {r['symbol']: r for r in records}, counts

    def test_symbols_split_into_class_method_and_kind(self):
        self.assertEqual(fi.split_symbol('??1Widget@@UAE@XZ'), ('Widget', '~Widget', 'dtor'))
        self.assertEqual(fi.split_symbol('??_GWidget@@UAEPAXI@Z'), ('Widget', '~Widget', 'deleting-dtor'))
        self.assertEqual(fi.split_symbol('??0Inner@Outer@@QAE@XZ'), ('Outer::Inner', 'Inner', 'ctor'))
        self.assertEqual(fi.split_symbol('?Count@Widget@@UBEHXZ'), ('Widget', 'Count', 'method'))
        self.assertEqual(fi.split_symbol('?FreeHelper@@YAHH@Z'), (None, 'FreeHelper', 'free'))
        self.assertEqual(fi.split_symbol('??4Widget@@QAEAAV0@ABV0@@Z'), ('Widget', 'operator=', 'operator'))

    def test_placeholders_and_optimisation(self):
        rec, _ = self.by_symbol()
        self.assertTrue(rec['?Poke@FUN_00401000_shell@@QAEXXZ']['placeholder'])
        self.assertTrue(rec['?vf12@Widget@@UAEXXZ']['placeholder'])
        self.assertFalse(rec['?Draw@Widget@@UAEXH@Z']['placeholder'])
        self.assertEqual(rec['?Draw@Widget@@UAEXH@Z']['opt'], '/O2')
        self.assertEqual(rec['?vf12@Widget@@UAEXXZ']['opt'], '/Od')
        self.assertEqual(fi.opt_level(['/Od', '/O2']), '/O2')

    def test_source_lines_from_definitions_and_inline_declarations(self):
        rec, _ = self.by_symbol()
        draw = rec['?Draw@Widget@@UAEXH@Z']
        self.assertEqual((draw['source'], draw['line'], draw['line_how']), ('src/core/widget.cpp', 12, 'definition'))
        self.assertEqual(draw['signature'], 'void Widget::Draw(int a)')
        flags = rec['?GetFlags@Widget@@QBEHXZ']
        self.assertEqual((flags['source'], flags['line'], flags['line_how']), ('include/Widget.h', 7, 'declaration'))
        self.assertEqual(rec['?FreeHelper@@YAHH@Z']['line'], 20)

    def test_slots_follow_the_primary_chain_and_need_every_header(self):
        headers = fi.header_classes(self.fnv)
        self.assertEqual(fi.fnv_slots('Widget', headers), ['~Widget', 'Tick', 'Count', 'Draw'])
        self.assertIsNone(fi.fnv_slots('Orphan', headers))
        rec, _ = self.by_symbol()
        self.assertEqual(rec['?Draw@Widget@@UAEXH@Z']['fnv_slot'], 3)
        self.assertEqual(rec['??_GWidget@@UAEPAXI@Z']['fnv_slot'], 0)
        self.assertIsNone(rec['??1Widget@@UAE@XZ']['fnv_slot'])

    def test_joins_by_name_and_by_slot(self):
        rec, counts = self.by_symbol()
        self.assertIn({'rva': 0x300, 'how': 'name'}, rec['?Count@Widget@@UBEHXZ']['ours'])
        self.assertIn({'rva': 0x300, 'how': 'slot', 'slot': 2, 'same_name': True}, rec['?Count@Widget@@UBEHXZ']['ours'])
        self.assertEqual(rec['?Draw@Widget@@UAEXH@Z']['ours'], [{'rva': 0x400, 'how': 'slot', 'slot': 3, 'same_name': None}])
        # The inherited slot 1 is not joined, and a placeholder name of ours joins nothing.
        self.assertFalse(any(o['rva'] in (0x200, 0x500) for r in rec.values() for o in r['ours']))
        self.assertEqual(counts['our functions joined only by slot'], 1)
        self.assertEqual(counts['slot pairs, names agree'], 2)

    def test_pack_section_lists_joins_and_small_methods(self):
        records, _ = fi.build(self.fnv, self.analysis)
        with open(self.analysis / ep.FNV_INDEX, 'w') as fh:
            for r in records:
                fh.write(json.dumps(r) + '\n')
        (self.analysis / 'fnv_index.meta.json').write_text(json.dumps({'revision': '91e1b6e8d8bb'}))
        text = '\n'.join(ep.sibling_lines('Widget', [0x300, 0x400, 0x999], root=self.analysis))
        self.assertIn('## Sibling source (momusdigital/fnv_decomp@91e1b6e8', text)
        self.assertIn('32-bit build of an older engine version', text)
        self.assertIn('`0x300`: `Widget::Count` `src/core/widget.cpp:7` (/O2, 3 bytes)', text)
        self.assertIn('`0x400`: `Widget::Draw`', text)
        self.assertIn('positional guess', text)
        self.assertIn('- `GetFlags` `include/Widget.h:7`', text)
        self.assertNotIn('Poke', text)
        self.assertNotIn('vf12', text)
        self.assertEqual(ep.sibling_lines('Nothing', [0x999], root=self.analysis), [])

    def test_pack_section_is_absent_without_an_index(self):
        self.assertEqual(ep.sibling_lines('Widget', [0x300], root=self.analysis), [])


if __name__ == '__main__':
    unittest.main()
