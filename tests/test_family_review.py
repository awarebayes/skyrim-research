"""Family acceptance on original synthetic leaf functions and a real local git history.

Comparator reports come from compare(), never a fabricated pass. No game input or runner.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import accept_function as af
import check
import family_review as fr
import flow
from compare import compare
from source_digest import tu_digest
from test_match_gate import GateFixture, CPP, HDR, MAP, PIN, RECORD, REVIEW
import synthetic_pecoff as fx


class FamilyReviewTests(GateFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        (self.root / RECORD).unlink()
        (self.root / REVIEW).unlink()
        self.fdir = self.root / '.local/flow'
        self.write('.gitignore', '.local/\n')
        self.write('tools/synthetic_template.py', 'def emit(value):\n    return value\n')
        self.template = hashlib.sha256((self.root / 'tools/synthetic_template.py').read_bytes()).hexdigest()
        self.origin = dict(family='synthetic-leaf', version='1', template_digest=self.template)
        self.write(CPP, '#include "SyntheticSum.h"\n' + '\n'.join(
            f'int SyntheticLeaf{i}(int x) {{ return x + 1; }}' for i in range(41)) + '\n')
        unit = fx.Unit()
        for i in range(41):
            sec = unit.section('.text$mn', fx.CALLEE_CODE, fx.SCN_TEXT)
            unit.define(f'SyntheticLeaf{i}', sec, storage=fx.STORAGE_EXTERNAL, function=True)
        self.image = unit.link({})
        self.target['image_sha256'] = hashlib.sha256(self.image).hexdigest()
        placement = unit.default_placement()
        symbols = {f'SyntheticLeaf{i}': {'rva': placement[i + 1], 'size': len(fx.CALLEE_CODE)} for i in range(41)}
        symbol_map = {'schema': 1, 'build_id': 'synthetic-fixture', 'folds': [], 'symbols': symbols}
        self.write(MAP, json.dumps(symbol_map))
        self.data['functions'] = []
        self.records = {}
        for i in range(41):
            rva = placement[i + 1]
            fn = dict(id=f'synthetic-fixture-0x{rva:x}', build_id='synthetic-fixture', rva=rva,
                      size=len(fx.CALLEE_CODE), status='mapped', name=f'SyntheticLeaf{i}', name_origin='GUESS',
                      owner='test', evidence='findings/synthetic.md', report=f'reports/synthetic-fixture/0x{rva:x}.json')
            self.fn = fn
            self.data['functions'].append(fn)
            reports = []
            for stamp in (1, 2):
                obj = bytearray(unit.coff())
                struct.pack_into('<I', obj, 4, stamp)
                args = fx.inputs(obj=bytes(obj), image=self.image, recipe_bytes=self.recipe_bytes)
                args['symbol_map'] = (self.root / MAP).read_bytes()
                args['task'].update(rva=rva, size=fn['size'], symbol=fn['name'], source_path=CPP,
                                    source_revision=tu_digest(self.root, [CPP, HDR]))
                args['build_record'].update(source_path=CPP, source_revision=args['task']['source_revision'])
                reports.append(compare(**args))
            self.record = self.make_record(runs=[('host-a', 'host-a', reports[0]), ('host-b', 'host-b', reports[1])])
            self.record.update(origin=copy.deepcopy(self.origin), family_parameters={'width': 4}, name_source='GUESS(low)')
            self.record['build'] = self.build_block()
            self.records[fn['id']] = self.record
            fr.write(self.root, fn['report'], self.record)
        self.write('builds/target.json', json.dumps(self.target))
        self.save_data()
        self.first = [fn['id'] for fn in self.data['functions'][:20]]
        self.later = [fn['id'] for fn in self.data['functions'][20:]]
        self.approve_members(self.first, 'initial')
        sample_fn = self.data['functions'][0]
        self.family = dict(family_schema=1, origin=self.origin, binding=fr.binding(sample_fn, self.records[self.first[0]]),
                           template_source={'path': 'tools/synthetic_template.py', 'sha256': self.template},
                           parameter_source={'path': 'tools/synthetic_template.py', 'sha256': self.template},
                           parameter_ranges={'width': {'min': 1, 'max': 8}}, first_members=self.first,
                           review=None, paused=False, pause_reason='')
        fr.write(self.root, '.local/family-spec.json', self.family)
        self.family_path = flow.plan_family(self.root, '.local/family-spec.json')
        self.family = fr.read(self.root, self.family_path)
        self.family_review_path = '.local/reviews/synthetic-family.family.json'
        self.family_doc = dict(family_review_schema=1, review_task_id='synthetic-family', reviewer_model='opus',
                               profile='cheap', spec_sha256=fr.digest(fr.spec(self.family)), fresh_context=True,
                               drafted_or_triaged=False, verdict='approve', escalation_category='none',
                               checks=dict.fromkeys(('plausible_source', 'provenance', 'claim_scope', 'publication_hygiene',
                                                     'parameter_extraction', 'target_binding', 'name_sources', 'first_20'), 'pass'))
        fr.write(self.root, self.family_review_path, self.family_doc)
        flow.approve_family(self.root, self.fdir, self.family_path, self.root / self.family_review_path)
        self.family = fr.read(self.root, self.family_path)
        self.git('init', '--quiet', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.commit('base')
        self.batch_path = flow.plan_family_batch(self.root, self.family_path, 'synthetic-batch', 'synthetic-seed', self.later)
        self.commit('record seed and population')
        self.batch = flow.draw_family_batch(self.root, self.batch_path)
        self.commit('record sample')
        self.unsampled = sorted(set(self.later) - set(self.batch['sample']))
        self.assertEqual(len(self.unsampled), 1)

    def test_individual_and_multi_review_acceptance_are_byte_identical(self):
        from datetime import datetime, timezone
        from contextlib import nullcontext
        from test_acceptance_flow import review_text
        when = datetime(2000, 1, 3, tzinfo=timezone.utc)
        requests = []
        for i, fid in enumerate(self.later):
            fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
            review = self.root / f'.local/reviews/batch-{i}.md'
            review.write_text(review_text(f'batch-{i}', [dict(rva=fn['rva'], size=fn['size'],
                                                           digest=self.records[fid]['source']['digest'])]))
            requests.append(dict(review=str(review), functions=[fid]))
        tracked = self.git('ls-files').splitlines()
        before = {name: (self.root / name).read_bytes() for name in tracked}
        # The old path invokes a complete acceptance transaction for each function, uncached.
        with patch.object(af, 'source_digest_cache', return_value=nullcontext()), \
                patch.object(check, 'include_closure', __import__('source_digest').include_closure):
            for request in requests:
                af.accept_many(self.root, request['review'], select=set(request['functions']), when=when)
        paths = set(tracked) | {p.relative_to(self.root).as_posix()
                               for p in (self.root / 'reports').rglob('*.json')}
        expected = {name: (self.root / name).read_bytes() for name in paths}
        for name in paths:
            if name in before:
                (self.root / name).write_bytes(before[name])
            else:
                (self.root / name).unlink()
        with patch.object(af, 'write_index', wraps=af.write_index) as index, \
                patch.object(af, 'validate_review', wraps=af.validate_review) as review_check:
            changed, skipped = af.accept_reviews(self.root, requests, when=when)
        self.assertEqual(index.call_count, 1)
        self.assertEqual(review_check.call_count, len(requests))
        self.assertEqual(skipped, [])
        self.assertEqual(sum(p.endswith('.review.json') for p in changed), len(requests))
        self.assertEqual(expected, {name: (self.root / name).read_bytes() for name in paths})
        check.validate(fr.read(self.root, 'data/progress.json'), self.target, self.root)

    def test_family_acceptance_rebuilds_index_once(self):
        self.ready()
        with patch.object(af, 'write_index', wraps=af.write_index) as index:
            self.accept_batch()
        self.assertEqual(index.call_count, 1)

    def test_generator_record_family_plan_roundtrip(self):
        from types import SimpleNamespace
        import importlib.util
        spec = importlib.util.spec_from_file_location("family_stamp", ROOT / "tools/stamp.py")
        stamp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stamp)
        from verifier import match_record
        template = ROOT / 'tools/stamp_template_v2.py'
        self.write('tools/stamp_template_v2.py', template.read_text())
        params = {'family': 'constant', 'width': 4, 'value': 1, 'virtual': False}
        metadata = stamp.family_metadata('const-return', params, 'GUESS(low)')
        header, source = stamp.template_v2.emit_leaf('Example', 'Read', family='constant',
                                                     width=4, value=1, virtual=False, name_label='GUESS(low)')
        self.assertIn('return 0x1;', source)
        self.assertIn('GUESS(low)', header)
        sample = self.records[self.first[0]]
        run_args = []
        for i, run in enumerate(sample['runs']):
            path = self.root / f'run-{i}.json'
            path.write_text(json.dumps(run['report']))
            run_args.append((run['compiled_on'], run['compared_on'], str(path)))
        build = self.root / 'build.json'
        build.write_text(json.dumps(sample['build']))
        for fid in self.first:
            fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
            args = SimpleNamespace(run=run_args, function_id=fid, unit=[CPP, HDR], compiled=CPP,
                                   recipe=sample['recipe']['path'], symbols=MAP, reproduction=sample['reproduction'],
                                   build=str(build), note=sample['notes'], family_metadata=json.dumps(metadata))
            record = match_record.build(args, self.root)
            # Keep each function's actual comparator reports from the synthetic fixture.
            record['runs'] = self.records[fid]['runs']
            fr.write(self.root, fn['report'], record)
        spec = dict(origin=metadata['origin'], binding=fr.binding(self.data['functions'][0], self.records[self.first[0]]),
                    template_source={'path': 'tools/stamp_template_v2.py', 'sha256': metadata['origin']['template_digest']},
                    parameter_source={'path': 'tools/stamp_template_v2.py', 'sha256': metadata['origin']['template_digest']},
                    parameter_ranges={k: {'values': [v]} for k, v in params.items()}, first_members=self.first)
        fr.write(self.root, '.local/generator-spec.json', spec)
        path = flow.plan_family(self.root, '.local/generator-spec.json')
        self.assertTrue((self.root / path).is_file())
        fn = self.data['functions'][0]
        record = fr.read(self.root, fn['report'])
        record['origin']['template_digest'] = 'f' * 64
        fr.write(self.root, fn['report'], record)
        with self.assertRaisesRegex(ValueError, 'family version or template digest mismatch'):
            flow.plan_family(self.root, '.local/generator-spec.json')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE, text=True).strip()

    def commit(self, message):
        self.git('add', '--all')
        self.git('commit', '--quiet', '-m', message)

    def save_data(self):
        fr.write(self.root, 'data/progress.json', self.data)

    def reload_data(self):
        self.data = fr.read(self.root, 'data/progress.json')

    def approve_members(self, ids, name):
        fns = [fn for fn in self.data['functions'] if fn['id'] in ids]
        rvas = [flow.hexrva(fn['rva']) for fn in fns]
        for second in (False, True):
            task = name + ('-s' if second else '')
            text = (f'# Review {task}\n\nreviewer_model: opus\nfresh_context: yes\n'
                    'drafted_or_triaged_any_reviewed_function: no\ngates_in_force: G2\nsource_revision: synthetic\n'
                    f'sampling_second_pass: {"yes" if second else "no"}\ndecompiler_output_read: no\n')
            for fn in fns:
                text += (f'\n## {fn["build_id"]} 0x{fn["rva"]:x} {fn["size"]}\n\nverdict: approve\n'
                         f'escalation_category: none\nsource_paths: {CPP} {HDR}\n'
                         f'source_digest: {self.records[fn["id"]]["source"]["digest"]}\nreport_path: {fn["report"]}\n'
                         'report_binding: agree\nchecks:\n  plausible_source: pass\n  provenance: pass\n'
                         '  claim_scope: pass\n  publication_hygiene: pass\nblocking_findings: none\n'
                         'naming_findings: none\nreasons: Original synthetic fixture.\n')
            self.write(f'.local/reviews/{task}.md', text)
            flow.save_group(self.fdir, dict(name=task, kind='sampling' if second else 'review', task_id=task,
                                            build_id='synthetic-fixture', functions=rvas, sampled=rvas,
                                            reviewer_model='opus', profile='cheap', pair=name + '-s',
                                            rerun={'not_agree': [], 'agree': rvas}))
        af.accept_many(self.root, self.root / f'.local/reviews/{name}.md')
        self.reload_data()

    def accept_batch(self):
        return af.accept_family_batch(self.root, self.batch_path, fdir=self.fdir, profile='cheap')

    def ready(self):
        self.approve_members(self.batch['sample'], 'sample')
        self.commit('accept independently reviewed sample')

    def assertRefused(self, pattern):
        before = (self.root / 'data/progress.json').read_bytes()
        with self.assertRaisesRegex((ValueError, af.Refused), pattern):
            self.accept_batch()
        self.assertEqual(before, (self.root / 'data/progress.json').read_bytes())
        fn = next(fn for fn in self.data['functions'] if fn['id'] == self.unsampled[0])
        self.assertFalse((self.root / check.review_record_path(fn)).exists())

    def test_acceptance_preserves_comparator_and_names_family_review(self):
        self.ready()
        self.accept_batch()
        self.reload_data()
        check.validate(self.data, self.target, self.root)
        fn = next(fn for fn in self.data['functions'] if fn['id'] == self.unsampled[0])
        rv = fr.read(self.root, check.review_record_path(fn))
        self.assertEqual(rv['review_kind'], 'family')
        self.assertEqual(rv['review_task_id'], 'synthetic-family')
        self.assertEqual(rv['review_sha256'], self.family['review']['review_sha256'])
        self.assertEqual(rv['family_evidence']['batch_sha256'], fr.digest(self.batch))
        self.assertFalse(fn['named'])

    def public_review_inputs(self):
        self.ready()
        self.accept_batch()
        self.reload_data()
        fn = next(fn for fn in self.data['functions'] if fn['id'] == self.unsampled[0])
        return fn, self.records[fn['id']], fr.read(self.root, check.review_record_path(fn))

    def test_public_metadata_validation_reuses_only_exact_contents(self):
        fn, record, review = self.public_review_inputs()
        fr._public_family_batch.cache_clear()
        with patch.object(fr, 'validate_family', wraps=fr.validate_family) as family_check, \
                patch.object(fr, 'validate_batch', wraps=fr.validate_batch) as batch_check, \
                patch.object(fr, 'check_member', wraps=fr.check_member) as member_check:
            for _ in range(2):
                fr.validate_public_review(self.root, fn, record, review)
            self.assertEqual(family_check.call_count, 1)
            self.assertEqual(batch_check.call_count, 1)
            self.assertEqual(member_check.call_count, 2)
        self.assertEqual(fr._public_family_batch.cache_info().maxsize, 8)

    def test_public_cache_rereads_same_size_same_mtime_changed_batch(self):
        fn, record, review = self.public_review_inputs()
        fr.validate_public_review(self.root, fn, record, review)
        path = self.root / self.batch_path
        before, stat = path.read_bytes(), path.stat()
        batch = copy.deepcopy(self.batch)
        batch['members'][fn['id']] = '0' * 64
        fr.write(self.root, self.batch_path, batch)
        self.assertEqual(len(path.read_bytes()), len(before))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'member differs from committed population'):
            fr.validate_public_review(self.root, fn, record, review)

    def test_public_cache_keeps_all_member_and_review_bindings(self):
        fn, record, review = self.public_review_inputs()
        fr.validate_public_review(self.root, fn, record, review)
        changed_record = copy.deepcopy(record)
        changed_record['family_parameters']['width'] = 5
        with self.assertRaisesRegex(ValueError, 'member differs from committed population'):
            fr.validate_public_review(self.root, fn, changed_record, review)
        changed_review = copy.deepcopy(review)
        changed_review['family_evidence']['member_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sanitized family evidence digest mismatch'):
            fr.validate_public_review(self.root, fn, record, changed_review)
        changed_review = copy.deepcopy(review)
        changed_review['review_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sanitized record names another family review'):
            fr.validate_public_review(self.root, fn, record, changed_review)

    def test_public_cache_does_not_hide_duplicate_fields_or_changed_paths(self):
        fn, record, review = self.public_review_inputs()
        fr.validate_public_review(self.root, fn, record, review)
        other_path = str(Path(self.family_path).with_name('other.json'))
        self.write(other_path, (self.root / self.family_path).read_text())
        changed_review = copy.deepcopy(review)
        changed_review['family_evidence']['family_path'] = other_path
        with self.assertRaisesRegex(ValueError, 'batch names another family'):
            fr.validate_public_review(self.root, fn, record, changed_review)
        path = self.root / self.batch_path
        path.write_text(path.read_text().replace('{', '{"batch_schema": 1,', 1))
        with self.assertRaisesRegex(ValueError, 'duplicate JSON field'):
            fr.validate_public_review(self.root, fn, record, review)

    def exact_row_audit_family(self, rows=None):
        family = copy.deepcopy(self.family)
        family.update(parameter_ranges=fr.exact_ranges(rows or [{'width': 4}]), review=None)
        fr.write(self.root, self.family_path, family)
        return family

    def test_family_packet_audits_every_row_and_is_read_only(self):
        import review_packet
        self.exact_row_audit_family()
        paths = [self.family_path, 'data/progress.json', self.data['functions'][0]['report']]
        before = {p: (self.root / p).read_bytes() for p in paths}
        result = '\n'.join(review_packet.family_rows(self.root, self.family_path))
        self.assertIn('permitted rows checked: 1/1; current reproduced members: 41', result)
        self.assertIn('does not re-extract target references', result)
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in paths})

    def test_family_packet_refuses_unrepresented_rows_and_changed_first_members(self):
        import review_packet
        self.exact_row_audit_family([{'width': 4}, {'width': 5}])
        with self.assertRaisesRegex(ValueError, '1 permitted row.*lack'):
            review_packet.family_rows(self.root, self.family_path)
        family = self.exact_row_audit_family()
        family['first_members'][self.first[0]] = '0' * 64
        fr.write(self.root, self.family_path, family)
        with self.assertRaisesRegex(ValueError, 'frozen first-20 member binding changed'):
            review_packet.family_rows(self.root, self.family_path)

    def test_family_packet_refuses_wrong_parameter_rva_and_stale_source(self):
        import review_packet
        family = copy.deepcopy(self.family)
        for fn in self.data['functions']:
            rec = self.records[fn['id']]
            rec['family_parameters'] = {'entry-rva': fn['rva'], 'size': fn['size']}
        self.records[self.later[-1]]['family_parameters']['entry-rva'] += 1
        for fn in self.data['functions']:
            fr.write(self.root, fn['report'], self.records[fn['id']])
        family.update(review=None, parameter_ranges=fr.exact_ranges(
            [r['family_parameters'] for r in self.records.values()]))
        family['first_members'] = {fn['id']: fr.member_digest(fn, self.records[fn['id']])
                                   for fn in self.data['functions'] if fn['id'] in self.first}
        fr.write(self.root, self.family_path, family)
        with self.assertRaisesRegex(ValueError, 'parameter entry-rva disagrees with inventory'):
            review_packet.family_rows(self.root, self.family_path)
        with (self.root / CPP).open('a') as out:
            out.write('// Changed fixture source.\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            review_packet.family_rows(self.root, self.family_path)

    def test_unreviewed_family(self):
        self.family['review'] = None
        fr.write(self.root, self.family_path, self.family)
        self.assertRefused('unreviewed family')

    def test_family_actions_waits_for_records_from_another_checkout(self):
        missing = next(fn for fn in self.data['functions'] if fn['id'] == self.later[0])
        missing.pop('report')
        self.save_data()
        actions = flow.family_actions(self.root, self.fdir)
        self.assertTrue(any(kind == 'wait' and 'needs local match records' in text for kind, text in actions))
        self.assertFalse(any('review-group' in text or 'integrate-family' in text for _, text in actions))
        before = (self.root / 'data/progress.json').read_bytes()
        with self.assertRaises((ValueError, KeyError, af.Refused)):
            self.accept_batch()
        self.assertEqual(before, (self.root / 'data/progress.json').read_bytes())

    def test_missing_saved_private_family_review(self):
        (self.root / self.family_review_path).unlink()
        self.assertRefused('saved approving family review missing')

    def test_digest_mismatch(self):
        self.family['origin']['template_digest'] = 'b' * 64
        fr.write(self.root, self.family_path, self.family)
        self.assertRefused('template digest mismatch')

    def test_sampled_member_without_review(self):
        self.assertRefused('sampled or first-20 member needs its own approving review')

    def test_paused_family(self):
        flow.pause_family(self.root, self.family_path, 'Synthetic defect under assessment.')
        self.assertRefused('family is paused')

    def test_sample_drawn_after_acceptance(self):
        self.ready()
        batch = dict(self.batch, sample=None, commitment=None)
        fr.write(self.root, self.batch_path, batch)
        self.commit('late population')
        with self.assertRaisesRegex(ValueError, 'sample drawn after an acceptance'):
            flow.draw_family_batch(self.root, self.batch_path)

    def test_out_of_range_parameter_needs_individual_review(self):
        self.ready()
        fid = self.unsampled[0]
        fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
        rec = self.records[fid]
        rec['family_parameters']['width'] = 9
        fr.write(self.root, fn['report'], rec)
        # Direct range enforcement rejects the exemption independently of the immutable row binding.
        with self.assertRaisesRegex(ValueError, 'outside reviewed ranges'):
            fr.check_member(self.family, fn, rec)
        self.assertRefused('member differs from committed population')

    def test_unadmitted_family_reviewer(self):
        self.family_doc['reviewer_model'] = 'sonnet'
        fr.write(self.root, self.family_review_path, self.family_doc)
        self.family['review']['reviewer_model'] = 'sonnet'
        self.family['review']['review_sha256'] = hashlib.sha256((self.root / self.family_review_path).read_bytes()).hexdigest()
        fr.write(self.root, self.family_path, self.family)
        self.assertRefused('not admitted')

    def test_tampered_sample_seed(self):
        self.batch['seed'] = 'different-seed'
        fr.write(self.root, self.batch_path, self.batch)
        self.assertRefused('tampered sample|commit the batch metadata')

    def test_tampered_sample_population(self):
        self.batch['population'].remove(self.unsampled[0])
        del self.batch['members'][self.unsampled[0]]
        self.batch['sample'] = fr.draw(self.batch['seed'], self.batch['population'])
        fr.write(self.root, self.batch_path, self.batch)
        self.assertRefused('commit the batch metadata')

    def test_recomputed_sample_cannot_replace_commitment(self):
        self.batch['seed'] = 'new-seed'
        self.batch['sample'] = fr.draw(self.batch['seed'], self.batch['population'])
        fr.write(self.root, self.batch_path, self.batch)
        self.assertRefused('commit the batch metadata')

    def test_uncommitted_draw(self):
        self.git('reset', '--quiet', 'HEAD^')
        self.assertRefused('commit the batch metadata')

    def test_second_pass_safeguard_is_required(self):
        self.ready()
        (self.root / '.local/reviews/sample-s.md').unlink()
        self.assertRefused('sampling safeguard')

    def test_changed_template_requires_new_family(self):
        self.write('tools/synthetic_template.py', 'def changed():\n    pass\n')
        self.assertRefused('start a new family')

    def test_flow_actions_draw_review_accept_and_pause(self):
        text = '\n'.join(t for _, t in flow.family_actions(self.root, self.fdir))
        self.assertIn('review sample', text)
        self.ready()
        self.assertIn('accept batch', '\n'.join(t for _, t in flow.family_actions(self.root, self.fdir)))
        flow.pause_family(self.root, self.family_path, 'Synthetic stop.')
        self.assertTrue(any(k == 'stop' and 'family paused' in t for k, t in flow.family_actions(self.root, self.fdir)))

    def test_member_origin_digest_mismatch(self):
        fid = self.unsampled[0]
        fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
        rec = self.records[fid]
        rec['origin']['template_digest'] = 'b' * 64
        fr.write(self.root, fn['report'], rec)
        self.assertRefused('family version or template digest mismatch')

    def test_absent_origin_label(self):
        fid = self.unsampled[0]
        fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
        rec = self.records[fid]
        del rec['origin']
        fr.write(self.root, fn['report'], rec)
        self.assertRefused('origin needs family')

    def test_binding_change_starts_new_family(self):
        fn = self.data['functions'][-1]
        for field in ('build_id', 'image_sha256', 'recipe_sha256', 'compiler', 'toolchain_sha256', 'comparator'):
            with self.subTest(field=field):
                family = copy.deepcopy(self.family)
                family['binding'][field] = 'different'
                with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                    fr.check_member(family, fn, self.records[fn['id']])

    def test_missing_name_source_label(self):
        fid = self.unsampled[0]
        fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
        rec = self.records[fid]
        del rec['name_source']
        fr.write(self.root, fn['report'], rec)
        self.assertRefused('name_source must be')

    def test_duplicate_family_review_field_is_refused(self):
        path = self.root / self.family_review_path
        blob = path.read_text().replace('"verdict": "approve"', '"verdict": "reject", "verdict": "approve"')
        path.write_text(blob)
        self.family['review']['review_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        fr.write(self.root, self.family_path, self.family)
        self.assertRefused('duplicate JSON field')

    def test_tampered_first_twenty_spec_invalidates_family_approval(self):
        self.family['first_members'][self.first[0]] = 'a' * 64
        fr.write(self.root, self.family_path, self.family)
        self.assertRefused('family review spec digest mismatch')

    def test_no_range_exemption_for_wrong_parameter_type(self):
        self.assertFalse(fr.in_ranges({'width': True}, self.family['parameter_ranges']))
        self.assertFalse(fr.in_ranges({'width': '4'}, self.family['parameter_ranges']))
        self.assertFalse(fr.in_ranges({}, self.family['parameter_ranges']))
        self.assertFalse(fr.in_ranges({'width': 4, 'other': 1}, self.family['parameter_ranges']))
        self.assertTrue(fr.in_ranges({'virtual': True}, {'virtual': {'values': [True]}}))
        self.assertFalse(fr.in_ranges({'virtual': 1}, {'virtual': {'values': [True]}}))

    def test_individual_review_keeps_per_function_rule(self):
        self.ready()
        self.approve_members(self.unsampled, 'individual')
        self.commit('accept remaining member by individual rule')
        self.assertEqual(self.accept_batch(), [])
        fn = next(fn for fn in self.data['functions'] if fn['id'] == self.unsampled[0])
        rv = fr.read(self.root, check.review_record_path(fn))
        self.assertEqual(rv['review_kind'], 'full')

    def test_out_of_range_committed_row_requires_and_allows_individual_review(self):
        self.git('reset', '--quiet', '--hard', 'HEAD^^')
        fid = self.unsampled[0]
        fn = next(fn for fn in self.data['functions'] if fn['id'] == fid)
        self.records[fid]['family_parameters']['width'] = 9
        fr.write(self.root, fn['report'], self.records[fid])
        flow.plan_family_batch(self.root, self.family_path, 'synthetic-batch', 'synthetic-seed', self.later)
        self.commit('record out-of-range member before selection')
        self.batch = flow.draw_family_batch(self.root, self.batch_path)
        self.commit('record sample before acceptance')
        self.ready()
        self.assertRefused('sampled or first-20 member needs its own approving review')
        self.approve_members([fid], 'individual')
        self.commit('accept out-of-range member by individual review')
        self.assertEqual(self.accept_batch(), [])


    def test_integrate_family_uses_isolated_tree_without_pushing(self):
        self.ready()
        remote = self.root / '.local/origin.git'
        self.git('init', '--quiet', '--bare', str(remote))
        self.git('remote', 'add', 'origin', str(remote))
        self.git('push', '--quiet', 'origin', 'main')
        ran = []

        def run(cmd, tree, step, env=None):
            ran.append(step)
            if step == 'accept_function.py':
                changed = af.accept_family_batch(tree, self.batch_path, fdir=self.fdir, profile='cheap')
                return 'changed files (stage these by name; nothing was committed):\n' + ''.join('  ' + p + '\n' for p in changed)
            if step in ('build_index.py', 'build_progress_svg.py'):
                return ''
            if step == 'build_model_trend.py':
                for path in ('README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg'):
                    (tree / path).parent.mkdir(parents=True, exist_ok=True)
                    (tree / path).write_text('synthetic trend\n')
                return ''
            if step == 'git commit':
                return flow.git(tree, *cmd[1:])
            if step == 'check.py --staged':
                check.validate(fr.read(tree, 'data/progress.json'), self.target, tree)
                return 'PASS'
            self.fail('unexpected command ' + step)

        with patch.object(flow, 'run', side_effect=run), patch.object(flow, 'pre_push_checks') as checks:
            group = flow.integrate_family(self.root, self.fdir, self.batch_path, push=False)
        result = group['integrated']
        self.assertIsNone(result['pushed'])
        self.assertEqual(ran, ['accept_function.py', 'build_index.py', 'build_progress_svg.py', 'build_model_trend.py', 'check.py --staged', 'git commit'])
        checks.assert_called_once()
        integrated = json.loads(self.git('show', result['commit'] + ':data/progress.json'))
        self.assertTrue(all(fn['status'] == 'matched' for fn in integrated['functions']))
        self.reload_data()
        self.assertTrue(any(fn['status'] != 'matched' for fn in self.data['functions']))
        self.assertNotEqual(result['commit'], self.git('rev-parse', 'origin/main'))


    def test_family_and_first_twenty_share_one_primary_review_pass(self):
        (self.root / self.batch_path).unlink()
        (self.root / self.family_path).unlink()
        shutil.rmtree(self.fdir / 'groups')
        for fn in self.data['functions']:
            if fn['id'] in self.first:
                fn['status'] = 'mapped'
                fn.pop('named', None)
                (self.root / check.review_record_path(fn)).unlink()
        self.save_data()
        path = flow.plan_family(self.root, '.local/family-spec.json', self.fdir)
        primaries = [g for g in flow.groups(self.fdir).values() if g['kind'] == 'review']
        self.assertEqual(len(primaries), 1)
        g = primaries[0]
        self.assertEqual(len(g['functions']), 20)
        self.assertEqual(g['family_review_path'], path)
        self.assertIn('docs/anti-eu-bureaucracy.md', (self.root / g['brief']).read_text())
        self.assertIn('in this same pass', (self.root / g['brief']).read_text())
        self.assertIn(str((self.root / '.local/analysis/fnv_index.jsonl').resolve()), (self.root / g['brief']).read_text())
        self.assertIn(str((self.root / '.local/packs').resolve()), (self.root / g['brief']).read_text())
        self.assertEqual(flow.review_group(self.root, self.fdir), [])
        actions = flow.family_actions(self.root, self.fdir)
        self.assertEqual(sum(k == 'dispatch' and 'family review needed' in t for k, t in actions), 1)
        flow.log_event(self.fdir, 'family-dispatched', task=g['task_id'], family=path)
        self.assertTrue(any(k == 'wait' for k, _ in flow.family_actions(self.root, self.fdir)))
        redone = flow.redo_review(self.root, self.fdir, g['name'])
        self.assertIn('-r2', redone['task_id'])
        self.assertIn('in this same pass', (self.root / redone['brief']).read_text())

    def test_supersede_unapproved_family_preserves_reviews_and_replans(self):
        (self.root / self.batch_path).unlink()
        (self.root / self.family_path).unlink()
        shutil.rmtree(self.fdir / 'groups')
        for fn in self.data['functions']:
            if fn['id'] in self.first:
                fn['status'] = 'mapped'
                fn.pop('named', None)
                (self.root / check.review_record_path(fn)).unlink()
        self.save_data()
        old_path = flow.plan_family(self.root, '.local/family-spec.json', self.fdir)
        flow.pause_family(self.root, old_path, 'Parameter range defect.')
        old = fr.read(self.root, old_path)
        group = next(g for g in flow.groups(self.fdir).values() if g['kind'] == 'review')
        review = self.root / '.local/reviews' / (group['task_id'] + '.md')
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text('saved reviewer evidence')
        family_review = review.with_suffix('.family.json')
        family_review.write_text('{"verdict":"escalate"}')
        spec = fr.read(self.root, '.local/family-spec.json')
        spec['parameter_ranges'] = fr.exact_ranges([{'width': 4}])
        fr.write(self.root, '.local/new-spec.json', spec)
        with patch('flow.review_group', side_effect=ValueError('synthetic refusal')):
            with self.assertRaisesRegex(ValueError, 'synthetic refusal'):
                flow.plan_family(self.root, '.local/new-spec.json', self.fdir, old_path)
        self.assertEqual(fr.read(self.root, old_path), old)
        self.assertTrue(review.is_file())
        self.assertFalse(flow.load_group(self.fdir, group['name']).get('superseded_by'))
        new_path = flow.plan_family(self.root, '.local/new-spec.json', self.fdir, old_path)
        self.assertNotEqual(old_path, new_path)
        self.assertEqual(fr.read(self.root, old_path)['superseded_by'], new_path)
        self.assertEqual(fr.read(self.root, new_path)['supersedes'], old_path)
        archive = self.root / '.local/reviews/superseded' / fr.family_key(old)
        self.assertEqual((archive / review.name).read_text(), 'saved reviewer evidence')
        self.assertTrue((archive / family_review.name).exists())
        self.assertFalse(review.exists())
        self.assertEqual(flow.load_group(self.fdir, group['name'])['superseded_by'], new_path)
        self.assertEqual(len([g for g in flow.groups(self.fdir).values()
                              if g['kind'] == 'review' and not g.get('superseded_by')]), 1)
        fr.validate_metadata(self.root)
        flow.family_group_hold(self.root, self.fdir, [self.first[0]])
        replacement = fr.read(self.root, new_path)
        replacement['binding']['image_sha256'] = 'f' * 64
        fr.write(self.root, new_path, replacement)
        with self.assertRaisesRegex(ValueError, 'supersession binding mismatch'):
            fr.validate_metadata(self.root)

    def test_supersede_approved_family_is_refused_without_changes(self):
        old = fr.read(self.root, self.family_path)
        with self.assertRaisesRegex(ValueError, 'never-approved'):
            flow.plan_family(self.root, '.local/family-spec.json', self.fdir, self.family_path)
        self.assertEqual(fr.read(self.root, self.family_path), old)
        self.assertTrue((self.root / self.family_review_path).is_file())

    def test_seed_population_must_be_committed_before_draw(self):
        self.git('reset', '--quiet', '--hard', 'HEAD^^')
        path = flow.plan_family_batch(self.root, self.family_path, 'synthetic-batch', 'synthetic-seed', self.later)
        actions = flow.family_actions(self.root, self.fdir)
        self.assertTrue(any(k == 'run' and 'family-draw' in t for k, t in actions))
        with self.assertRaisesRegex(ValueError, 'commit the batch metadata'):
            flow.draw_family_batch(self.root, path)


    def test_sample_rejection_holds_entire_family_and_prints_pause(self):
        self.ready()
        path = self.root / '.local/reviews/sample.md'
        path.write_text(path.read_text().replace('verdict: approve', 'verdict: reject', 1))
        self.assertRefused('sample rejection or escalation')
        self.assertTrue(any(k == 'stop' and 'family-pause' in t for k, t in flow.family_actions(self.root, self.fdir)))

    def test_second_reviewer_disagreement_holds_entire_family(self):
        self.ready()
        path = self.root / '.local/reviews/sample-s.md'
        path.write_text(path.read_text().replace('verdict: approve', 'verdict: reject', 1))
        self.assertRefused('sampling disagreement')


    def test_draw_size_and_reproducibility(self):
        for n, count in ((1, 1), (19, 19), (20, 20), (21, 20), (1000, 50), (1001, 51)):
            population = [f'synthetic-{i}' for i in range(n)]
            self.assertEqual(len(fr.draw('seed', population)), count)
            self.assertEqual(fr.draw('seed', population), fr.draw('seed', list(reversed(population))))

    def test_family_record_cannot_be_relabelled_without_family_gate(self):
        self.ready()
        self.accept_batch()
        self.reload_data()
        fn = next(fn for fn in self.data['functions'] if fn['id'] == self.unsampled[0])
        rv = fr.read(self.root, check.review_record_path(fn))
        rv['family_evidence']['batch_sha256'] = 'a' * 64
        fr.write(self.root, check.review_record_path(fn), rv)
        with self.assertRaisesRegex(ValueError, 'evidence digest mismatch'):
            check.validate(self.data, self.target, self.root)


if __name__ == '__main__':
    unittest.main()


class ExactParameterRowsTests(unittest.TestCase):
    def test_preserves_correlated_rows_and_types(self):
        a = {'width': 1, 'value': 2, 'virtual': True}
        b = {'width': 4, 'value': 1000, 'virtual': True}
        ranges = fr.exact_ranges([a, b, a])
        self.assertEqual(len(ranges['rows']), 2)
        for row in (a, b):
            self.assertTrue(fr.in_ranges(row, ranges))
        for row in ({'width': 1, 'value': 1000, 'virtual': True},
                    {'width': 4, 'value': 2, 'virtual': True},
                    {'width': 1, 'value': 2, 'virtual': 1},
                    {'width': 1, 'value': 2},
                    {'width': 1, 'value': 2, 'virtual': True, 'extra': 0}):
            self.assertFalse(fr.in_ranges(row, ranges))

    def test_refuses_invalid_or_duplicate_rows(self):
        for rows in ([], [{}], [{'x': 1}, {'y': 1}], [{'x': 1}, {'x': 1}], [{'x': None}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                fr.validate_ranges({'rows': rows})
