"""tools/analysis/clusters.py and stamp.py on synthetic records and class names (no game data)."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'analysis'))
import clusters  # noqa: E402
import lint_reconstruction  # noqa: E402
import stamp  # noqa: E402
import x64  # noqa: E402


def rec(rva, masked, exact, size=11, targets=(), owner=None, name=None, template=False):
    return {'rva': rva, 'masked': masked, 'exact': exact, 'shape': masked, 'size': size, 'targets': list(targets),
            'operands': [], 'owner': owner, 'name': name, 'template': template, 'eh': False, 'flags': []}


class ClusterTests(unittest.TestCase):
    def test_partition_and_summary(self):
        rs = [rec(0x30, 'a', 'x'), rec(0x10, 'a', 'y'), rec(0x20, 'a', 'x'), rec(0x40, 'b', 'z', size=5)]
        parts = clusters.partition(rs, 'masked')
        self.assertEqual([r['rva'] for r in parts['a']], [0x10, 0x20, 0x30])
        s = clusters.level_summary(parts)
        self.assertEqual((s['repeats'], s['repeat_bytes'], s['singletons']), (2, 22, 1))
        self.assertEqual(s['buckets']['3-4'], {'clusters': 1, 'functions': 3, 'bytes': 33})
        self.assertEqual(clusters.level_summary(clusters.partition(rs, 'exact'))['repeats'], 1)

    def test_columns_and_cases(self):
        ms = [rec(1, 'a', 'p', targets=[(3, 'REL32', 0x500), (9, 'REL32', 0x900)], owner='Alpha'),
              rec(2, 'a', 'q', targets=[(3, 'REL32', 0x600), (9, 'REL32', 0x900)], owner='Beta')]
        self.assertEqual(clusters.columns(ms), [(3, 'REL32', True), (9, 'REL32', False)])
        self.assertEqual(clusters.stamp_case(ms), 'class-methods')
        tm = [dict(m, template=True, owner='Sink<%s>' % m['owner']) for m in ms]
        self.assertEqual(clusters.stamp_case(tm), 'template')
        dup = [rec(1, 'a', 'p', targets=[(3, 'REL32', 0x500)]), rec(2, 'a', 'q', targets=[(3, 'REL32', 0x500)])]
        self.assertEqual(clusters.stamp_case(dup), 'duplicate-helper')
        self.assertEqual(clusters.stamp_case(ms[:1] + dup[1:]), 'unowned')
        self.assertTrue(clusters.stampable({'owner': None, 'name': None}, 'unowned', ['vftable:Alpha']))
        self.assertFalse(clusters.stampable({'owner': None, 'name': None}, 'unowned', [None]))

    def test_score_prefers_named_and_solved(self):
        row = {'members': 11, 'size': 40, 'named': 0, 'stampable': 11, 'case': 'class-methods'}
        base = clusters.score(row)
        self.assertGreater(clusters.score(dict(row, named=11)), base)
        self.assertEqual(clusters.score(row, 'accepted'), 3 * base)
        self.assertLess(clusters.score(dict(row, case='duplicate-helper')), base)

    def test_describe_shapes(self):
        def insns(hexes):
            out, off = [], 0
            code = b''.join(bytes.fromhex(h) for h in hexes)
            for h in hexes:
                ins = x64.decode(code, off, off)
                out.append((off, ins))
                off += ins.length
            return out, code
        self.assertIn('offset 0x28', clusters.describe(*insns(['488b4128', 'c3']), {}))
        self.assertEqual(clusters.describe(*insns(['c3']), {}), 'empty function (returns at once)')
        self.assertIn('adjustor', clusters.describe(*insns(['4883e908', 'e900000000']), {}))
        dd = ['53', '4883ec20', '488d0500000000', '488bd9', '488901', 'f6c201', '740a', 'ba08000000',
              'e800000000', '488bc3', '4883c420', '5b', 'c3']
        self.assertIn('deleting destructor', clusters.describe(*insns(dd), {}))


class TypeNameTests(unittest.TestCase):
    def test_plain_namespaced_template(self):
        tn = stamp.parse_type_descriptor('.?AVWidget@@')
        self.assertEqual((tn.keyword, tn.qualified, tn.template), ('class', 'Widget', False))
        self.assertEqual(stamp.decorated('dtor', tn), '??1Widget@@UEAA@XZ')
        self.assertEqual(stamp.decorated('deleting-dtor', tn), '??_GWidget@@UEAAPEAXI@Z')
        self.assertEqual(stamp.decorated('vftable', tn), '??_7Widget@@6B@')
        tn = stamp.parse_type_descriptor('.?AUFilter@Tools@@')
        self.assertEqual((tn.keyword, tn.qualified, tn.leaf, tn.namespaces), ('struct', 'Tools::Filter', 'Filter', ['Tools']))
        tn = stamp.parse_type_descriptor('.?AV?$Sink@UEvent@@@@')
        self.assertEqual(tn.qualified, 'Sink<Event>')
        self.assertEqual(stamp.decorated('dtor', tn), '??1?$Sink@UEvent@@@@UEAA@XZ')
        self.assertEqual(stamp.forward_decls(tn), ['struct Event;'])
        tn = stamp.parse_type_descriptor('.?AV?$Pool@VItem@@$0BA@@@')
        self.assertEqual(tn.args, ['Item', '16'])
        self.assertEqual(stamp.param_kinds(tn.args), ['class', 'int'])
        tn = stamp.parse_type_descriptor('.?AV?$Creator@V?$Handler@VActor@@H@@@@')
        self.assertEqual(tn.args, ['Handler<Actor, int>'])
        self.assertIn('template <class, class> class Handler;', stamp.forward_decls(tn))
        with self.assertRaises(stamp.Unsupported):
            stamp.parse_type_descriptor('.?AVHidden@?A0x1234abcd@@')


class EmitTests(unittest.TestCase):
    """Generated units pass the repository lint when placed in a tree with the cited evidence."""

    def lint_tree(self, dest):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'builds', root / 'builds')
            (root / 'reconstruction').mkdir()
            shutil.copytree(ROOT / 'reconstruction' / 'recipes', root / 'reconstruction' / 'recipes')
            (root / 'findings').mkdir()
            (root / stamp.EVIDENCE).write_text('evidence placeholder\n')
            for p in (Path(dest) / 'reconstruction').rglob('*'):
                if p.is_file():
                    target = root / 'reconstruction' / p.relative_to(Path(dest) / 'reconstruction')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(p, target)
            return lint_reconstruction.lint_tree(root)

    def test_root_derived_and_family_units(self):
        rows = [
            {'kind': 'root', 'vftable': '0x9000', 'base_dtor': ['0x1000'], 'deleting_dtor': ['0x1100'],
             'type_descriptor': '.?AVBSWidget@@', 'area': 'bsengine',
             'symbols': {'??_7BSWidget@@6B@': '0x9000', '??1BSWidget@@UEAA@XZ': '0x1000',
                         '??_GBSWidget@@UEAAPEAXI@Z': '0x1100'}},
            {'kind': 'derived', 'vftable': '0x9100', 'stored_vftable': '0x9000', 'base_dtor': [],
             'deleting_dtor': ['0x1200'], 'type_descriptor': '.?AVBSGadget@@', 'base_type_descriptor': '.?AVBSWidget@@',
             'area': 'bsengine', 'symbols': {'??_GBSGadget@@UEAAPEAXI@Z': '0x1200', '??_7BSWidget@@6B@': '0x9000'}},
            {'kind': 'root', 'vftable': '0x9200', 'base_dtor': ['0x1300'], 'deleting_dtor': [],
             'type_descriptor': '.?AV?$BSTSink@UEventA@@@@', 'area': 'bsengine',
             'symbols': {'??1?$BSTSink@UEventA@@@@UEAA@XZ': '0x1300'}},
            {'kind': 'root', 'vftable': '0x9300', 'base_dtor': ['0x1400'], 'deleting_dtor': [],
             'type_descriptor': '.?AV?$BSTSink@UEventB@@@@', 'area': 'bsengine',
             'symbols': {'??1?$BSTSink@UEventB@@@@UEAA@XZ': '0x1400'}},
            {'kind': 'root', 'skip': 'secondary vftable', 'vftable': '0x9400', 'base_dtor': [], 'deleting_dtor': []},
        ]
        with tempfile.TemporaryDirectory() as dest:
            out = stamp.emit_dtor_family(rows, dest, ['m:aaaa', 'm:bbbb'], '0x2000', 'reconstruction/x/Y.cpp',
                                         delete_rva='0x7000')
            self.assertEqual(sorted(e['class'] for e in out), ['BSGadget', 'BSTSink', 'BSWidget'])
            self.assertEqual(self.lint_tree(dest), [])
            task = json.loads((Path(dest) / 'tasks' / 'stamp-aaaa-bswidget' / 'task.json').read_text())
            self.assertEqual([f['symbol'] for f in task['functions']], ['??1BSWidget@@UEAA@XZ', '??_GBSWidget@@UEAAPEAXI@Z'])
            syms = json.loads((Path(dest) / 'tasks' / 'stamp-aaaa-bswidget' / 'symbols.json').read_text())['symbols']
            self.assertEqual(syms[stamp.SIZED_DELETE]['rva'], 0x7000)
            src = (Path(dest) / 'reconstruction' / 'bsengine' / 'BSTSink.cpp').read_text()
            self.assertIn('template class BSTSink<EventA>;', src)
            self.assertIn('template class BSTSink<EventB>;', src)
            self.assertIn('Generated by tools/analysis/stamp.py from exemplar 0x2000',
                          (Path(dest) / 'reconstruction' / 'bsengine' / 'BSGadget.h').read_text())

    def test_template_file_fill(self):
        self.assertEqual(stamp.fill('void {Leaf}::F() { {col:0x11}::F(); }', {'Leaf': 'A', 'col:0x11': 'B'}),
                         'void A::F() { B::F(); }')
        with self.assertRaises(KeyError):
            stamp.fill('{Missing}', {})


if __name__ == '__main__':
    unittest.main()
