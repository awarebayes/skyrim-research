"""Internal-function identity and full-section refusals, using original synthetic inputs only."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import tempfile

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'tools'),
                str(Path(__file__).resolve().parents[1] / 'tools/verifier')]
import compare_internal as ci
from compare import compare as legacy_compare
from pecoff import CoffObject
import synthetic_pecoff as fx
from test_match_gate import GateFixture, CPP, HDR, MAP, RECORD, compiled_object
from check import validate_match
from source_digest import tu_digest
import unit_build
import pipeline
import verify_function as vf


def internalize(args, symbol=None):
    """Give an existing synthetic fixture an internal primary function and a fully pinned task."""
    args = copy.deepcopy(args)
    name = symbol or args['task']['symbol']
    blob = bytearray(args['object_bytes'])
    obj = CoffObject(blob)
    sym = next(s for s in obj.symbols.values() if s.name == name and s.section > 0)
    table = struct.unpack_from('<I', blob, 8)[0]
    blob[table + 18 * sym.index + 16] = 3
    obj = CoffObject(blob)
    sym = obj.symbols[sym.index]
    revision = fx.sha256(b'original synthetic translation unit')
    args['task']['source_revision'] = revision
    args['build_record']['source_revision'] = revision
    args['object_bytes'] = bytes(blob)
    args['build_record']['object_sha256'] = fx.sha256(blob)
    args['task']['task_schema'] = 2
    args['task']['internal_identity'] = ci.make_identity(blob, name, ci.selector(obj, sym), revision,
                                                        args['task']['source_path'])
    return args


class InternalComparatorTests(unittest.TestCase):
    def assertRejected(self, args, reason):
        report = ci.compare(**args)
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['reason'], reason, report['detail'])

    def test_opt_in_complete_section(self):
        args = internalize(fx.inputs())
        self.assertEqual(legacy_compare(**args)['reason'], 'candidate-boundary-unsupported')
        report = ci.compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual((report['report_schema'], report['contract_version']), (2, 3))
        self.assertEqual(report['function']['internal_identity'], args['task']['internal_identity'])

    def test_verify_wrapper_dispatches_the_versioned_task(self):
        args = internalize(fx.inputs())
        private = Path(ci.ROOT / '.local').resolve()
        private.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=private) as tmp:
            root = Path(tmp)
            files = {'task.json': {'verify_task_schema': 2, 'task': args['task'],
                                  'recipe': 'recipe.json', 'symbols': 'symbols.json', 'manifest': 'manifest.json'},
                     'manifest.json': args['manifest'], 'symbols.json': args['symbol_map'],
                     'build.json': args['build_record']}
            for name, data in files.items():
                (root / name).write_text(json.dumps(data))
            for name, data in [('recipe.json', args['recipe_bytes']), ('candidate.obj', args['object_bytes']),
                               ('image.dll', args['image_bytes'])]:
                (root / name).write_bytes(data)
            code, _ = vf.run(root / 'task.json', root / 'candidate.obj', root / 'build.json', root / 'image.dll',
                             root / 'report.json', diagnostics=root / 'diagnostics.json')
            self.assertEqual(code, 0)
            self.assertEqual(json.loads((root / 'report.json').read_text())['contract_version'], 3)
            files['task.json']['verify_task_schema'] = 1
            (root / 'task.json').write_text(json.dumps(files['task.json']))
            with self.assertRaises(vf.TaskFileError):
                vf.load_task_file(root / 'task.json')

    def test_wrong_tu_and_changed_source(self):
        for field in ('source_revision', 'source_path'):
            args = internalize(fx.inputs())
            args['task'][field] = fx.sha256(b'another TU') if field == 'source_revision' else 'other.cpp'
            args['build_record'][field] = args['task'][field]
            self.assertRejected(args, 'internal-identity-mismatch')

    def test_wrong_pinned_object(self):
        args = internalize(fx.inputs())
        args['task']['internal_identity']['object_sha256'] = 'f' * 64
        self.assertRejected(args, 'internal-identity-mismatch')

    def test_wrong_section_and_symbol_kind(self):
        for field, value in (('section_number', 2), ('section_name', '.text$wrong'),
                             ('entry_offset', 1), ('storage_class', 2), ('symbol_type', 0)):
            args = internalize(fx.inputs())
            args['task']['internal_identity'][field] = value
            ident = args['task']['internal_identity']
            ident['map_key'] = ci.local_key(args['task']['source_revision'], args['task']['source_path'],
                                            args['task']['symbol'], {k: ident[k] for k in ci.SELECTOR_FIELDS})
            self.assertRejected(args, 'function-symbol-missing' if field.startswith('section_')
                                else 'candidate-boundary-unsupported')

    def test_truncated_and_overlong(self):
        for delta in (-1, 1):
            args = internalize(fx.inputs())
            args['task']['size'] += delta
            self.assertRejected(args, 'function-size-mismatch')

    def test_same_name_locals_resolve_by_section_not_table_index(self):
        u = fx.Unit()
        a = u.section('.text$mn', b'\xc3', fx.SCN_TEXT)
        b = u.section('.text$mn', b'\xc3', fx.SCN_TEXT)
        u.define('local', a, function=True)
        u.define('local', b, function=True)
        args = internalize(fx.unit_inputs(u, 'local', {}))
        self.assertEqual(ci.compare(**args)['result'], 'pass')
        u.symbols.reverse()
        other = internalize(fx.unit_inputs(u, 'local', {}))
        # The selector distinguishes the same spelling and independent sections in this object.
        self.assertNotEqual(args['task']['internal_identity']['map_key'],
                            other['task']['internal_identity']['map_key'])
        # Reordering the table never changes a given section's identity.
        co = CoffObject(other['object_bytes'])
        sym = next(s for s in co.symbols.values() if s.section == a)
        self.assertEqual(ci.symbol_key(co, sym, args['task']), args['task']['internal_identity']['map_key'])

    def test_ambiguous_symbol_and_absorbed_procedure(self):
        for offset in (0, 1):
            u = fx.Unit(); sec = u.section('.text$mn', b'\x90\xc3', fx.SCN_TEXT)
            u.define('local', sec, function=True)
            u.define('local' if offset == 0 else 'neighbour', sec, offset, function=True)
            args = internalize(fx.unit_inputs(u, 'local', {}))
            self.assertRejected(args, 'function-symbol-ambiguous' if offset == 0
                                else 'candidate-boundary-unsupported')

    def references(self):
        u = fx.Unit()
        f = u.section('.text$mn', bytes.fromhex('488d0d00000000e800000000e800000000c3'), fx.SCN_TEXT)
        u.define('local', f, function=True)
        d = u.section('.data', b'\0' * 8, 0xC0300040)
        u.define('guard', d)
        u.define('other_guard', d, 4)
        u.external('construct'); u.external('atexit')
        u.reloc(f, 3, 'guard', fx.REL32)
        u.reloc(f, 8, 'construct', fx.REL32); u.reloc(f, 13, 'atexit', fx.REL32)
        args = internalize(fx.unit_inputs(u, 'local', {'construct': 0x1100, 'atexit': 0x1110},
                                        extra_map={'guard': {'rva': 0x3000, 'size': 4},
                                                   'atexit': {'rva': 0x1110, 'size': None}}))
        co = CoffObject(args['object_bytes'])
        guard = next(s for s in co.symbols.values() if s.name == 'guard')
        key = ci.symbol_key(co, guard, args['task'])
        args['symbol_map']['symbols'][key] = args['symbol_map']['symbols'].pop('guard')
        return args, key

    def test_local_guard_requires_scoped_key_no_name_fallback(self):
        args, key = self.references()
        self.assertEqual(ci.compare(**args)['result'], 'pass')
        args['symbol_map']['symbols']['guard'] = args['symbol_map']['symbols'].pop(key)
        self.assertRejected(args, 'unresolved-symbol')

    def test_wrong_guard_atexit_and_reordered_cleanup(self):
        args, key = self.references()
        for name in (key, 'atexit'):
            bad = copy.deepcopy(args); bad['symbol_map']['symbols'][name]['rva'] += 4
            self.assertRejected(bad, 'relocation-target-mismatch')
        # Same instructions and targets, reversed relocation order: never a masked pass.
        bad = copy.deepcopy(args); blob = bytearray(bad['object_bytes']); co = CoffObject(blob)
        pos = co.section(1).reloc_ptr + 10
        a, b = struct.unpack_from('<I', blob, pos + 4)[0], struct.unpack_from('<I', blob, pos + 14)[0]
        struct.pack_into('<I', blob, pos + 4, b); struct.pack_into('<I', blob, pos + 14, a)
        bad['object_bytes'] = bytes(blob); bad['build_record']['object_sha256'] = fx.sha256(blob)
        bad['task']['internal_identity']['object_sha256'] = fx.sha256(blob)
        self.assertRejected(bad, 'relocation-target-mismatch')

    def test_existing_eh_and_unaccounted_funclet_checks_apply(self):
        args = internalize(fx.catch_inputs())
        report = ci.compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        unit = fx.catch_unit()
        funclet = fx.section_rva(unit, '?catch$0@?0??SyntheticCatch@@4HA')
        bad = internalize(fx.catch_inputs(unit, drop_pdata=(funclet,)))
        self.assertRejected(bad, 'unwind-coverage-extra')
        bad = internalize(fx.catch_inputs(fx.catch_unit(unrelocated_action=True)))
        self.assertRejected(bad, 'eh-unrelocated-reference')

    def test_tls_rules_and_iat_slot_equality_are_preserved(self):
        args = internalize(fx.tls_inputs())
        report = ci.compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        tls = next(e for e in args['symbol_map']['symbols'].values() if e.get('kind') == 'thread-local')
        tls['tls_offset'] += 4
        self.assertRejected(args, 'relocation-target-mismatch')
        unit = fx.Unit()
        sec = unit.section('.text$mn', bytes.fromhex('ff1500000000c3'), fx.SCN_TEXT)
        unit.define('local', sec, function=True)
        unit.external('__imp_SyntheticImport'); unit.reloc(sec, 2, '__imp_SyntheticImport', fx.REL32)
        args = internalize(fx.unit_inputs(unit, 'local', {'__imp_SyntheticImport': 0x3100}))
        self.assertEqual(ci.compare(**args)['result'], 'pass')
        args['symbol_map']['symbols']['__imp_SyntheticImport']['rva'] += 8
        self.assertRejected(args, 'relocation-target-mismatch')

    def test_local_definition_cannot_disguise_tls_index(self):
        unit = fx.tls_unit(define_index=True)
        unit.symbols = [(n, v, sec, kind, 3 if n == fx.TLS_INDEX else storage)
                        for n, v, sec, kind, storage in unit.symbols]
        args = internalize(fx.tls_inputs(unit))
        obj = CoffObject(args['object_bytes'])
        sym = next(s for s in obj.symbols.values() if s.name == fx.TLS_INDEX)
        args['symbol_map']['symbols'][ci.symbol_key(obj, sym, args['task'])] = {'rva': fx.TLS_INDEX_RVA, 'size': 4}
        self.assertRejected(args, 'unsupported-relocation')

    def test_scoped_guard_cannot_be_borrowed_from_another_tu(self):
        args, key = self.references()
        new_revision = fx.sha256(b'other translation unit with same local names')
        args['task']['source_revision'] = args['build_record']['source_revision'] = new_revision
        obj = CoffObject(args['object_bytes']); sym = next(s for s in obj.symbols.values() if s.name == 'local')
        args['task']['internal_identity'] = ci.make_identity(args['object_bytes'], sym.name,
            ci.selector(obj, sym), new_revision, args['task']['source_path'])
        self.assertRejected(args, 'unresolved-symbol')

    def test_alias_and_fold_guards_apply_to_scoped_function(self):
        args = internalize(fx.inputs())
        key = args['task']['internal_identity']['map_key']
        symbols = args['symbol_map']['symbols']
        symbols[key] = {'rva': args['task']['rva'], 'size': args['task']['size']}
        symbols['alias'] = dict(symbols[key])
        self.assertRejected(args, 'undeclared-alias')
        args['symbol_map']['folds'] = [[key, 'alias']]
        self.assertEqual(ci.compare(**args)['result'], 'pass')
        symbols['interior'] = {'rva': args['task']['rva'] + 1, 'size': 1}
        self.assertRejected(args, 'overlapping-function')

    def test_unit_spec_and_task_schema_are_versioned(self):
        args = internalize(fx.inputs()); ident = args['task']['internal_identity']
        value = {k: ident[k] for k in ci.SELECTOR_FIELDS}
        task = {'task_id': 'test', 'build_id': 'test', 'compiled': 'test.cpp', 'recipe': 'recipe.json',
                'symbols_repo': None, 'functions': [dict(args['task'], internal_selector=value)]}
        self.assertEqual(pipeline.unit_spec(task, {}, 'test')['unit_spec_schema'], 2)
        args['task']['task_schema'] = 1
        self.assertRejected(args, 'invalid-task')

    def test_build_task_carries_source_and_object_identity(self):
        args = internalize(fx.inputs()); ident = args['task']['internal_identity']
        value = {k: ident[k] for k in ci.SELECTOR_FIELDS}
        spec = {'build_id': args['task']['build_id'], 'image_sha256': args['task']['target_image_sha256'],
                'compiled': args['task']['source_path']}
        fn = dict(args['task'], internal_selector=value)
        task = unit_build.make_task(spec, fn, args['task']['source_revision'], args['task']['recipe_sha256'],
                                    args['object_bytes'])
        self.assertEqual(task['internal_identity'], ident)


class InternalGateTests(GateFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        smap = json.loads((self.root / MAP).read_text()); del smap['symbols'][fx.FUNCTION]
        reports = []
        for stamp in (1, 2):
            args = internalize(fx.inputs(obj=compiled_object(stamp), image=self.image, recipe_bytes=self.recipe_bytes))
            revision = tu_digest(self.root, [CPP, HDR]); args['task'].update(source_revision=revision, source_path=CPP)
            args['build_record'].update(source_revision=revision, source_path=CPP)
            co = CoffObject(args['object_bytes']); sym = next(iter(co.symbols.values()))
            args['task']['internal_identity'] = ci.make_identity(args['object_bytes'], sym.name, ci.selector(co, sym), revision, CPP)
            key = args['task']['internal_identity']['map_key']
            smap['symbols'][key] = {'rva': self.fn['rva'], 'size': self.fn['size']}
            args['symbol_map'] = json.dumps(smap).encode()
            report = ci.compare(**args); self.assertEqual(report['result'], 'pass', report['detail'])
            reports.append(report)
        self.write(MAP, json.dumps(smap))
        # Use exactly the bytes the comparator read as the map pin.
        self.write(MAP, args['symbol_map'])
        self.record = self.make_record([('host-a', 'host-a', reports[0]), ('host-b', 'host-b', reports[1])])
        self.record['match_record_schema'] = 3; self.save_record()

    def test_two_host_internal_record_passes_consistency_only(self):
        validate_match(self.fn, self.target, self.root)
        self.assertGateRejects('Internal prototype cannot be accepted')

    def test_acceptance_tool_refuses_consistent_prototype(self):
        from test_accept_function import AcceptFunctionTests, REVIEW_FILE
        from test_match_gate import REVIEW
        import accept_function as af
        self.fn['status'] = 'reconstructed'
        (self.root / REVIEW).unlink()
        self.write('data/progress.json', json.dumps(self.data))
        self.write('builds/target.json', json.dumps(self.target))
        AcceptFunctionTests.write_review(self)
        before = (self.root / 'data/progress.json').read_bytes()
        with self.assertRaisesRegex(af.Refused, 'Internal prototype cannot be accepted'):
            af.accept(self.root, 'synthetic-fixture', self.fn['rva'], self.root / REVIEW_FILE, 'approve')
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), before)
        self.assertFalse((self.root / REVIEW).exists())

    def test_changed_identity_on_second_host_rejected(self):
        self.record['runs'][1]['report']['function']['internal_identity']['section_number'] += 1
        self.save_record(); self.assertGateRejects('internal identity')

    def test_wrong_object_and_schema_rejected(self):
        self.record['runs'][0]['report']['function']['internal_identity']['object_sha256'] = 'e' * 64
        self.save_record(); self.assertGateRejects('another object')

    def test_changed_source_and_single_host_records_rejected(self):
        self.write(HDR, 'int changed_source;\n')
        self.assertGateRejects('Stale acceptance|source digest is stale')

    def test_internal_record_requires_both_compile_hosts(self):
        self.record['runs'][1]['compiled_on'] = 'host-a'
        self.save_record(); self.assertGateRejects('at least 2 compile hosts')

    def test_different_consistent_selector_on_second_host_rejected(self):
        report = self.record['runs'][1]['report']; ident = report['function']['internal_identity']
        ident['section_number'] += 1
        ident['map_key'] = ci.local_key(ident['source_revision'], ident['source_path'],
            report['function']['symbol'], {k: ident[k] for k in ci.SELECTOR_FIELDS})
        self.save_record(); self.assertGateRejects('different internal identities')

    def test_legacy_schema_cannot_carry_internal_report(self):
        self.record['match_record_schema'] = 2; self.save_record()
        self.assertGateRejects('schema or contract')
