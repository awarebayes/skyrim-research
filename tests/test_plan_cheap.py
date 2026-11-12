"""The low-cost planner (tools/ghidra/plan_cheap.py), multi-unit task directories written by
export_pack.py and the group view of tools/verifier/attempt, on synthetic inputs only: every table
row, byte string and task below is invented for the test."""
from importlib.machinery import SourceFileLoader
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'ghidra'))
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import export_pack as ep  # noqa: E402
import plan_cheap  # noqa: E402


def load_attempt():
    loader = SourceFileLoader('attempt_script', str(ROOT / 'tools' / 'verifier' / 'attempt'))
    spec = importlib.util.spec_from_loader('attempt_script', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def row(rva, cls, size=20, callers=1, l1=None, eh=None, cluster=1):
    return {'rva': rva, 'kind': 'ordinary', 'size': size, 'callers': callers, 'l1': l1 or f'k{rva}',
            'cluster_size': cluster, 'v2': {'verdict': 'supported', 'reasons': [], 'cautions': []},
            'eh': {'handler': eh, 'handler_kind': 'c++' if eh else None, 'states': None, 'try_blocks': None},
            'owner': {'class': cls, 'how': 'vtable', 'slot': 1},
            'names': [{'name': f'{cls}::F{rva:x}', 'source': 'ng-slot', 'how': 'slot 1'}]}


def cls(ancestors, size=0x40, passes=('ng',), area='forms'):
    return {'ancestors': list(ancestors), 'size': size, 'passes': list(passes), 'area': area, 'slots': [1]}


CLASSES = {
    'TESForm': cls([]),
    'TESAlpha': cls(['TESForm']), 'TESBeta': cls(['TESForm']), 'TESGamma': cls(['TESForm']),
    'TESDelta': cls(['TESForm']), 'TESNoSize': cls(['TESForm'], size=None),
    'NiObject': cls([], area='netimmerse'), 'NiBig': cls(['NiObject'], area='netimmerse'),
}


def opts(**kw):
    base = {'total': 100, 'small_task_min': 4, 'small_task_max': 6, 'small_task_floor': 3, 'normal_min': 3,
            'normal_max': 4, 'normal_functions': 10, 'small_per_class': 3}
    base.update(kw)
    return base


class PlanTests(unittest.TestCase):
    def rows(self):
        rows = []
        for i, c in enumerate(('TESAlpha', 'TESBeta', 'TESGamma', 'TESDelta')):
            rows += [row(0x1000 + 0x100 * i + j, c, size=16 + j) for j in range(3)]
        rows += [row(0x2000 + j, 'NiBig', size=100 + j) for j in range(5)]
        return rows

    def plan(self, rows, **kw):
        return plan_cheap.plan(rows, CLASSES, set(), opts(**kw), ep.table_eligibility)

    def test_rejections(self):
        rows = self.rows()
        rows += [row(0x3000, 'TESAlpha', eh=0x1234), row(0x3001, 'TESAlpha'), row(0x3002, 'TESAlpha'),
                 row(0x3003, 'TESNoSize'), row(0x3004, 'TESSkip')]
        classes = dict(CLASSES, TESSkip=cls(['TESForm']))
        tasks, stats = plan_cheap.plan(rows, classes, set(), opts(parked={0x3001}, tls={0x3002},
                                                                   skip_classes={'TESSkip'}), ep.table_eligibility)
        rej = stats['rejections']
        self.assertEqual(rej['exception-handling data'], 1)
        self.assertEqual(rej['parked family (census)'], 1)
        self.assertEqual(rej['thread-local reference'], 1)
        self.assertEqual(rej['class has no verified skeleton'], 1)
        self.assertEqual(rej['class has a unit or an open task'], 1)
        chosen = {f['rva'] for t in tasks for u in t['units'] for f in u['functions']}
        self.assertFalse(chosen & {0x3000, 0x3001, 0x3002, 0x3003, 0x3004})

    def test_small_and_normal_tasks(self):
        tasks, stats = self.plan(self.rows())
        kinds = {t['kind'] for t in tasks}
        self.assertEqual(kinds, {'small', 'normal'})
        normal = [t for t in tasks if t['kind'] == 'normal']
        self.assertEqual(len(normal), 1)
        self.assertEqual(normal[0]['units'][0]['class'], 'NiBig')
        self.assertEqual(len(normal[0]['units'][0]['functions']), 4)  # normal_max
        self.assertEqual(normal[0]['budget'], 3 * 4 + 4)
        for t in tasks:
            if t['kind'] != 'small':
                continue
            n = sum(len(u['functions']) for u in t['units'])
            self.assertLessEqual(n, 6)
            self.assertGreaterEqual(n, 3)
            self.assertEqual(t['family'], 'TESForm')
            self.assertEqual(len({u['class'] for u in t['units']}), len(t['units']))  # one unit per class
            for u in t['units']:
                self.assertTrue(u['task_id'].startswith(t['id'][:20]))
                self.assertEqual(u['budget'], max(3, 2 * len(u['functions'])))
                self.assertRegex(u['task_id'], r'^[a-z0-9][a-z0-9.-]{0,55}$')
        self.assertEqual(stats['functions'], 12 + 4)

    def test_one_function_per_cluster_and_total(self):
        rows = self.rows()
        rows.append(row(0x1001 + 0x5000, 'TESAlpha', l1='k4097'))  # same L1 key as 0x1001
        tasks, _ = self.plan(rows, total=8, normal_functions=4)
        chosen = [f['rva'] for t in tasks for u in t['units'] for f in u['functions']]
        self.assertEqual(len(chosen), len(set(chosen)))
        self.assertLessEqual(len(chosen), 8)
        self.assertFalse({0x1001, 0x6001} <= set(chosen))

    def test_fnv_counterpart_ranks_first(self):
        rows = self.rows()
        tasks, _ = self.plan(rows, fnv_rvas={0x1302}, small_per_class=1)
        delta = [u for t in tasks for u in t['units'] if u['class'] == 'TESDelta'][0]
        self.assertEqual(delta['functions'][0]['rva'], 0x1302)

    def test_chunk_never_splits_a_class(self):
        units = [('A', [1, 2, 3]), ('B', [1, 2, 3]), ('C', [1])]
        groups = plan_cheap.chunk(units, 4, 5)
        self.assertEqual([[c for c, _ in g] for g in groups], [['A'], ['B', 'C']])

    def test_tls_scan(self):
        blobs = {0x10: b'\x90\x65\x48\x8b\x04\x25\x58\x00\x00\x00\xc3', 0x20: b'\x48\x8b\x04\x25\x58\x00\x00\x00\xc3'}
        found = plan_cheap.tls_rvas(lambda rva, n: blobs[rva], [{'rva': 0x10, 'size': 11}, {'rva': 0x20, 'size': 9}])
        self.assertEqual(found, {0x10})

    def test_composition(self):
        tasks, _ = self.plan(self.rows(), fnv_rvas={0x1000})
        comp = plan_cheap.composition(tasks, CLASSES, {0x1000}, ep.area_for)
        self.assertEqual(comp['functions'], 16)
        self.assertEqual(comp['fnv_counterpart'], 1)
        self.assertEqual(sum(comp['size_bands'].values()), 16)


class ListAndBriefTests(unittest.TestCase):
    def test_parse_list_line(self):
        rva, tid, unit, recipe, group, budget = ep.parse_list_line(
            'b 0x10 batch5-s01-x-tesalpha reconstruction/forms/TESAlpha.cpp group=batch5-s01-x budget=4', 'b')
        self.assertEqual((rva, tid, unit, recipe, group, budget),
                         (0x10, 'batch5-s01-x-tesalpha', 'reconstruction/forms/TESAlpha.cpp', None, 'batch5-s01-x', 4))
        with self.assertRaises(SystemExit):
            ep.parse_list_line('b 0x10 t group=Bad_Group', 'b')
        with self.assertRaises(SystemExit):
            ep.parse_list_line('other 0x10 t', 'b')

    def test_listing_traits(self):
        listing = ('  +0x000  MOV EAX,dword ptr [RCX + 0x10]\n  +0x003  SHR EAX,0x3   \n  +0x006  TEST AL,0x1\n'
                   '  +0x008  LEA R8,[RSP + 0x30]\n  +0x00d  CALL 0x1234\n  +0x012  TEST RAX,RAX\n')
        traits = ep.listing_traits(listing, {'community_name': 'TESAlpha::~TESAlpha'})
        self.assertEqual(traits, ['flag-test', 'out-param', 'small-out-param', 'deleting-dtor', 'null-test'])
        self.assertEqual(ep.listing_traits('  +0x000  RET\n', {}), [])
        self.assertTrue(set(traits) <= set(ep.COOKBOOK_RULES))

    def test_shared_headers(self):
        packs = [{'build_id': 'b', 'references': [{'community_names': [{'name': 'TESBeta::Get'}]}]}]
        got = ep.shared_headers('TESAlpha', packs, {'TESForm': 'forms/TESForm.h', 'TESBeta': 'forms/TESBeta.h',
                                                    'TESAlpha': 'forms/TESAlpha.h'}, CLASSES)
        self.assertEqual(got, [('TESForm', 'forms/TESForm.h'), ('TESBeta', 'forms/TESBeta.h')])


class GroupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.gdir = self.tmp / '.local' / 'tasks' / 'batch9-s01-tesform'
        self.units = []
        for c, n in (('TESAlpha', 2), ('TESBeta', 1)):
            d = self.gdir / f'batch9-s01-tesform-{c.lower()}'
            d.mkdir(parents=True)
            fns = [{'rva': hex(0x100 * (i + 1)), 'size': 10 * (i + 1), 'symbol': 'unbound:x',
                    'community_name': f'{c}::F{i}'} for i in range(n)]
            (d / 'task.json').write_text(json.dumps({'task_id': d.name, 'compiled': f'reconstruction/forms/{c}.cpp',
                                                     'build_id': 'b', 'recipe': 'reconstruction/recipes/r.json',
                                                     'functions': fns, 'max_attempts': max(3, 2 * n)}))
            (d / 'BRIEF.md').write_text(f'# Brief: {d.name}\n\nUnit line\nOrder (smallest first): x\n1. `0x100`\n'
                                        'Known risks:\n- Class and member names are COMMUNITY\n## Sibling source\n')
            self.units.append(d)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_write_group_and_brief(self):
        group = ep.write_group(self.gdir, self.units)
        self.assertEqual(group['functions'], 3)
        self.assertEqual(group['max_attempts'], 4 + 3)
        saved = json.loads((self.gdir / 'group.json').read_text())
        self.assertEqual([u['dir'] for u in saved['units']], [u.name for u in self.units])
        brief = (self.gdir / 'BRIEF.md').read_text()
        self.assertIn('small task: 2 units, 3 functions', brief)
        self.assertIn('### Sibling source', brief)
        self.assertNotIn('Known risks:', brief)
        self.assertEqual(brief.count('Class and member names are COMMUNITY'), 1)
        self.assertEqual(brief.count('Body origin:'), 1)
        # Smallest unit first.
        self.assertLess(brief.index('## batch9-s01-tesform-tesbeta'), brief.index('## batch9-s01-tesform-tesalpha'))

    def test_refresh_briefs_keeps_attempt_history(self):
        ep.write_group(self.gdir, self.units)
        history = json.dumps({'attempt': 1, 'counted': True}) + '\n'
        (self.units[0] / 'attempts.jsonl').write_text(history)
        done = ep.refresh_briefs([self.gdir])
        self.assertIn(self.gdir / 'BRIEF.md', done)
        self.assertEqual((self.units[0] / 'attempts.jsonl').read_text(), history)
        for u in self.units:
            self.assertIn(ep.ORIGIN_LINE, (u / 'BRIEF.md').read_text())
        self.assertEqual((self.gdir / 'BRIEF.md').read_text().count('Body origin:'), 1)

    def test_attempt_prints_group_state(self):
        ep.write_group(self.gdir, self.units)
        unit = self.units[0]
        (unit / 'attempts.jsonl').write_text(json.dumps({'attempt': 1, 'counted': True}) + '\n'
                                             + json.dumps({'attempt': 2, 'counted': False}) + '\n')
        (unit / 'attempts' / '002').mkdir(parents=True)
        (unit / 'attempts' / '002' / 'attempt.txt').write_text('attempt 2 x (y); counted 1/4: 2/2 pass; includes\n')
        attempt = load_attempt()
        lines = attempt.group_status(self.gdir)
        self.assertIn('2 units, 3 functions', lines[0])
        self.assertIn('counted 1/4; last: 2/2 pass; includes', lines[1])
        self.assertIn('counted 0/3; last: not attempted', lines[2])


if __name__ == '__main__':
    unittest.main()
