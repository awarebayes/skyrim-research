"""Ordinary runtime EH support on original synthetic fixtures only."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'tools'),
                str(Path(__file__).resolve().parents[1] / 'tools/verifier')]
import compare as legacy
import compare_runtime as runtime
from pecoff import CoffObject, PeImage, Reject
import synthetic_pecoff as fx
import test_compare_internal as internal_tests
from test_match_gate import GateFixture, CPP, HDR, MAP, compiled_object
from source_digest import tu_digest
import bind


def inputs(**kwargs):
    args = internal_tests.RuntimeTerminationActionTests().inputs(**kwargs)
    blob = bytearray(args['object_bytes']); obj = CoffObject(blob)
    sym = next(s for s in obj.symbols.values() if s.name == fx.CATCH_FUNCTION)
    table = struct.unpack_from('<I', blob, 8)[0]
    blob[table + 18 * sym.index + 16] = 2
    args['object_bytes'] = bytes(blob)
    args['build_record']['object_sha256'] = fx.sha256(blob)
    args['task'].pop('internal_identity'); args['task'].pop('task_schema')
    return args


class RuntimeEH(unittest.TestCase):
    def assertFails(self, args, reason='eh-runtime-import'):
        report = runtime.compare(**args)
        self.assertEqual((report['result'], report['reason']), ('fail', reason), report['detail'])

    def test_ordinary_runtime_action_passes_with_complete_import_proof(self):
        args = inputs(); report = runtime.compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['comparator']['version'], runtime.COMPARATOR_VERSION)
        self.assertEqual(report['coverage']['runtime_actions'][0]['iat_rva'], 0x2DC0)
        self.assertEqual(runtime.termination_thunk(PeImage(args['image_bytes'])), {'rva': 0x1170, 'size': 6})
        self.assertEqual(legacy.compare(**args)['reason'], 'eh-reference-not-local')
        self.assertEqual(legacy.COMPARATOR_VERSION, '0.6.0')

    def test_wrong_module_name_ordinal_and_ambiguity_refuse(self):
        for kwargs in ({'module': b'OtherRuntime.dll'}, {'name': b'other_terminate'},
                       {'ordinal': True}, {'extra_import': True}):
            with self.subTest(kwargs=kwargs):
                self.assertFails(inputs(**kwargs))

    def test_thunk_iat_and_bound_import_mutations_refuse(self):
        fixture = internal_tests.RuntimeTerminationActionTests()
        for rva, data in ((0x1170, bytes((0xFF, 0x15))), (0x1172, struct.pack('<i', 0x2DC8-0x1176)),
                          (0x2D04, struct.pack('<I', 1)), (0x2DC0, struct.pack('<Q', 0x2E10))):
            args = inputs(); fixture.patch_image(args, rva, data); self.assertFails(args)

    def test_map_must_pin_exact_rva_and_six_bytes(self):
        for size in (None, 5, 7):
            args = inputs(); args['symbol_map']['symbols']['__std_terminate']['size'] = size
            self.assertFails(args)
        args = inputs(); args['symbol_map']['symbols']['__std_terminate']['rva'] += 1
        self.assertFails(args, 'eh-reference-mismatch')

    def test_other_external_action_stays_refused(self):
        args = fx.catch_inputs(fx.catch_unit(external_action='OtherRuntime'), fx.image_externals(OtherRuntime=0x1170))
        self.assertFails(args, 'eh-reference-not-local')

    def test_different_eh_state_is_still_a_real_mismatch(self):
        args = inputs(); blob = bytearray(args['object_bytes']); obj = CoffObject(blob)
        symbol = next(s for s in obj.symbols.values() if s.name == '$stateUnwindMap$SyntheticCatch')
        struct.pack_into('<i', blob, obj.section(symbol.section).raw_ptr + symbol.value, -2)
        args['object_bytes'] = bytes(blob); args['build_record']['object_sha256'] = fx.sha256(blob)
        self.assertFails(args, 'eh-data-mismatch')

    def test_binder_seeds_only_verified_unique_runtime_thunk(self):
        args = inputs()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); task = root/'task'; task.mkdir()
            (root/'object').write_bytes(args['object_bytes']); (root/'image').write_bytes(args['image_bytes'])
            (task/'task.json').write_text(json.dumps({'symbols':'symbols.json','functions':[]}))
            (task/'symbols.json').write_text(json.dumps({'schema':1,'symbols':{}}))
            report = bind.bind(task, root/'object', image_path=root/'image', repo=root)
            self.assertTrue(report['changed'])
            self.assertEqual(json.loads((task/'symbols.json').read_text())['symbols']['__std_terminate'],
                             {'rva':0x1170,'size':6})

    def test_duplicate_import_thunks_cannot_seed_a_binding(self):
        args = inputs()
        internal_tests.RuntimeTerminationActionTests().patch_image(args, 0x1180, bytes((0xFF,0x25)) + struct.pack('<i',0x2DC0-0x1186))
        with self.assertRaises(Reject): runtime.termination_thunk(PeImage(args['image_bytes']))

    def test_code_and_eh_integer_differences_remain_failures(self):
        args = inputs(); image = bytearray(args['image_bytes']); pe=PeImage(image)
        sec=pe.section_for(args['task']['rva']);image[sec.raw_ptr+args['task']['rva']-sec.vaddr] ^= 1
        args['image_bytes']=bytes(image);args['task']['target_image_sha256']=args['manifest']['image_sha256']=fx.sha256(image)
        self.assertFails(args, 'code-byte-mismatch')


class RuntimeGate(GateFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        runs=[]
        for stamp, host in ((1,'host-a'),(2,'host-b')):
            args=fx.inputs(obj=compiled_object(stamp),image=self.image,recipe_bytes=self.recipe_bytes)
            digest=tu_digest(self.root,[CPP,HDR]);args['task'].update(source_revision=digest,source_path=CPP)
            args['build_record'].update(source_revision=digest,source_path=CPP)
            args['symbol_map']=(self.root/MAP).read_bytes()
            runs.append((host,host,runtime.compare(**args)))
        self.record=self.make_record(runs);self.save_record()

    def test_new_engine_is_pinned_without_changing_legacy_engine(self):
        self.check()
        self.assertEqual(legacy.compare(**fx.inputs())['comparator']['version'],'0.6.0')

    def test_mixed_engines_and_unknown_hash_are_refused(self):
        self.record['runs'][1]['report']['comparator']['version']=legacy.COMPARATOR_VERSION
        self.save_record();self.assertGateRejects('different comparator version')

    def test_corrupt_runtime_coverage_is_refused(self):
        self.record['runs'][0]['report']['coverage']['runtime_actions']=[{'symbol':'OtherRuntime'}]
        self.save_record();self.assertGateRejects('runtime action identity')

    def test_malformed_first_run_still_reports_a_gate_refusal(self):
        self.record['runs'][0] = 'invalid'
        self.save_record(keep_build=True); self.assertGateRejects('each run names')
