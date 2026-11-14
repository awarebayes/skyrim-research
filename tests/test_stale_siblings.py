"""Per-member stale-sibling attribution; comparator and whole-tree gates are unchanged."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import accept_function as af
import check
from compare import compare
import family_review as fr
import flow
import flow_lane as lane
import lane_accept
from source_digest import tu_digest
import synthetic_pecoff as fx
import test_acceptance_batch as batches
from test_match_gate import CPP, HDR, MAP

INDEPENDENT = 'reconstruction/synthetic/Independent.cpp'


class StaleSiblingTests(unittest.TestCase):
    def setUp(self):
        self.case = batches.AcceptanceBatchTests('runTest')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root, self.fixture = self.case.root, self.case.fx
        self.baseline = copy.deepcopy(af.load(self.root)[0])
        self.bad, self.good = self.fixture.later[:2]

    def record(self, fid, compiled, unit_paths):
        fn = next(f for f in self.fixture.data['functions'] if f['id'] == fid)
        unit = fx.Unit()
        for row in self.fixture.data['functions']:
            section = unit.section('.text$mn', fx.CALLEE_CODE, fx.SCN_TEXT)
            unit.define(row['name'], section, storage=fx.STORAGE_EXTERNAL, function=True)
        digest = tu_digest(self.root, unit_paths)
        reports = []
        for stamp in (1, 2):
            obj = bytearray(unit.coff())
            struct.pack_into('<I', obj, 4, stamp)
            args = fx.inputs(obj=bytes(obj), image=self.fixture.image, recipe_bytes=self.fixture.recipe_bytes)
            args['symbol_map'] = (self.root / MAP).read_bytes()
            args['task'].update(rva=fn['rva'], size=fn['size'], symbol=fn['name'],
                                source_path=compiled, source_revision=digest)
            args['build_record'].update(source_path=compiled, source_revision=digest)
            reports.append(compare(**args))
        self.fixture.fn = fn
        record = self.fixture.make_record(runs=[('host-a', 'host-a', reports[0]), ('host-b', 'host-b', reports[1])])
        record['source'].update(compiled=compiled, translation_unit=unit_paths, digest=digest)
        record.update(origin=copy.deepcopy(self.fixture.origin), family_parameters={'width': 4}, name_source='GUESS(low)')
        self.fixture.record = record
        record['build'] = self.fixture.build_block()
        self.fixture.records[fid] = record
        fr.write(self.root, fn['report'], record)
        af.validate_match(dict(fn, status='matched'), self.fixture.target, self.root)

    def approve(self, fid, name, compiled):
        original = af.accept_many
        def accept(root, review, *args, **kwargs):
            for path in (Path(review), Path(review).with_name(name + '-s.md')):
                path.write_text(path.read_text().replace(f'source_paths: {CPP} {HDR}',
                                                        f'source_paths: {compiled} {HDR}'))
            return original(root, review, *args, **kwargs)
        with patch.object(af, 'accept_many', side_effect=accept):
            self.fixture.approve_members([fid], name)

    def changed_inputs(self):
        original = (self.root / CPP).read_text()
        (self.root / CPP).write_text(original + '// Original synthetic unit change.\n')
        (self.root / INDEPENDENT).write_text(original + '// Original independent unit.\n')
        # Unmatched reports are refreshed too; only the twenty pre-existing matched
        # siblings intentionally retain their old digest in this fixture.
        for fid in self.fixture.later:
            if fid != self.good:
                self.record(fid, CPP, [CPP, HDR])
        self.record(self.good, INDEPENDENT, [INDEPENDENT, HDR])
        self.approve(self.bad, 'bad-unit', CPP)
        self.approve(self.good, 'good-unit', INDEPENDENT)
        data = af.load(self.root)[0]
        by_id = {f['id']: f for f in data['functions']}
        return [dict(kind='review', group=name, item=name, build_id='synthetic-fixture',
                     functions=[flow.hexrva(by_id[fid]['rva'])],
                     review=str(self.root / f'.local/reviews/{name}.md'), profile='cheap')
                for fid, name in ((self.bad, 'bad-unit'), (self.good, 'good-unit'))]

    def test_shared_unit_is_dropped_but_independent_member_is_retained(self):
        requests = self.changed_inputs()
        with patch.object(af, 'acceptance_staleness', wraps=af.acceptance_staleness) as stale:
            accepted, dropped = lane.stale_sibling_members(self.root, self.baseline, requests)
        self.assertEqual(accepted, requests[1:])
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]['reason'], 'stale-sibling: needs re-confirm')
        self.assertEqual(dropped[0]['units'], [CPP])
        self.assertEqual(dropped[0]['stale_sibling_units'], [CPP])
        self.assertEqual(stale.call_count, 1, 'the twenty matched siblings share one unit scan')
        # This is attribution, not a weaker validator: the unfiltered tree still fails its guard.
        with self.assertRaisesRegex(ValueError, 'Stale acceptance'):
            check.validate(af.load(self.root)[0], self.fixture.target, self.root)

    def test_committed_family_selection_is_held_atomically(self):
        requests = self.changed_inputs()
        family = dict(requests[0], kind='family', functions=requests[0]['functions'] + requests[1]['functions'])
        accepted, dropped = lane.stale_sibling_members(self.root, self.baseline, [family])
        self.assertFalse(accepted)
        self.assertEqual(dropped[0]['request'], family)
        self.assertEqual(dropped[0]['reason'], 'stale-sibling: needs re-confirm')

    def test_unchanged_sibling_records_allow_an_unrelated_new_file(self):
        (self.root / INDEPENDENT).write_text('// Original synthetic unrelated file.\n')
        fn = self.fixture.data['functions'][20]
        requests = [dict(kind='review', build_id='synthetic-fixture', functions=[flow.hexrva(fn['rva'])])]
        accepted, dropped = lane.stale_sibling_members(self.root, self.baseline, requests)
        self.assertEqual(accepted, requests)
        self.assertFalse(dropped)

    def test_real_lane_drops_stale_unit_and_ships_independent_approval(self):
        remote = self.root / '.local/origin.git'
        self.fixture.git('init', '--quiet', '--bare', str(remote))
        self.fixture.git('remote', 'add', 'origin', str(remote))
        self.fixture.git('push', '--quiet', 'origin', 'main')
        original = self.fixture.git('rev-parse', 'HEAD')
        self.changed_inputs()
        items = [lane.enqueue(self.root, self.fixture.fdir, 'review', [name]) for name in ('bad-unit', 'good-unit')]
        receipt = dict(id='synthetic-stale-sibling', root=str(self.root), branch='main', items=items,
                       tooling=[], state='running', integrated=None)
        real_run = flow.run
        def run(cmd, tree, step, env=None):
            if step in ('build_progress_svg.py', 'build_model_trend.py'):
                paths = ('docs/progress.svg', 'docs/progress-map.svg') if step == 'build_progress_svg.py' else (
                    'README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg')
                for name in paths:
                    path = tree / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('Original synthetic generated output\n')
                return ''
            if step == 'check.py --staged':
                check.validate(fr.read(tree, af.PROGRESS), self.fixture.target, tree)
                return 'PASS'
            return real_run(cmd, tree, step, env=env)
        with patch.object(lane.resource_admission, 'admit'), patch.object(flow, 'run', side_effect=run), \
                patch.object(lane, 'accept', side_effect=lambda tree, requests, python:
                             lane_accept.accept(tree, requests, self.case.when)):
            lane.build(self.root, self.fixture.fdir, receipt, sys.executable, 'main')
        self.assertEqual(len(receipt['dropped']), 1, repr(receipt['dropped']))
        self.assertEqual(receipt['dropped'][0]['reason'], 'stale-sibling: needs re-confirm')
        self.assertEqual(receipt['integrated']['accepted'], 1)
        tree = Path(receipt['tree'])
        final = fr.read(tree, af.PROGRESS)
        status = {f['id']: f['status'] for f in final['functions']}
        self.assertEqual(status[self.bad], 'mapped')
        self.assertEqual(status[self.good], 'matched')
        self.assertEqual((tree / CPP).read_bytes(), self.fixture.git('show', original + ':' + CPP).encode() + b'\n')
        check.validate(final, self.fixture.target, tree)
        self.assertEqual(self.fixture.git('--git-dir', str(remote), 'rev-parse', 'main'), original)
