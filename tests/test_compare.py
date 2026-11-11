"""Comparator contract v2: positive cases and a rejection test for each failure it must catch."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare import ROOT, compare, sanitized
from pecoff import Reject
import synthetic_pecoff as fx


def run(**overrides):
    args = fx.inputs()
    args.update(overrides)
    return compare(**args)


class ComparatorTests(unittest.TestCase):
    def assertRejected(self, report, reason, detail=None):
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['reason'], reason, report['detail'])
        if detail:
            self.assertIn(detail, report['detail'])

    def test_fixture_link_matches_hand_computed_displacement(self):
        # call at +0x06 ends at 0x1010 + 0x0b; the callee is at 0x1000, so rel32 = -0x1b.
        image = fx.pe_image()
        text = image[0x400 + 0x10:0x400 + 0x10 + len(fx.CODE)]
        self.assertEqual(struct.unpack_from('<i', text, 7)[0], -0x1B)

    def test_positive_case_passes_with_full_coverage(self):
        report = run()
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual(cov['code_bytes_total'], len(fx.CODE))
        self.assertEqual(cov['code_bytes_exact'] + cov['code_bytes_by_reference'], len(fx.CODE))
        self.assertEqual(cov['code_bytes_by_reference'], 12)
        self.assertEqual(cov['relocations_by_type'], {'REL32': 2, 'REL32_1': 1})
        self.assertEqual((cov['unwind'], cov['unwind_entries'], cov['unwind_bytes_exact']), ('covered', 1, 8))
        self.assertEqual(report['acceptance'], 'not-evaluated')
        self.assertNotIn('matched', json.dumps(report))

    def test_report_carries_required_identity(self):
        args = fx.inputs()
        report = compare(**args)
        self.assertEqual(report['source']['source_revision'], args['task']['source_revision'])
        self.assertEqual(report['target']['image_sha256'], args['task']['target_image_sha256'])
        self.assertEqual(report['recipe']['flags'], ['/O2', '/Gy'])
        self.assertEqual(len(report['recipe']['compiler_binary_sha256']), 64)
        self.assertEqual(report['comparator']['version'], '0.2.0')
        self.assertEqual(report['contract_version'], 2)
        self.assertEqual(report['function'], {'build_id': 'synthetic-fixture', 'rva': 0x1010,
                                              'size': len(fx.CODE), 'symbol': fx.FUNCTION})

    def test_changed_byte_rejected(self):
        # 0x28 -> 0x38 in `sub rsp, imm8`, a byte no relocation covers.
        report = run(**fx.inputs(image=fx.pe_image(patch={3: 0x38})))
        self.assertRejected(report, 'code-byte-mismatch', '+0x3')

    def test_wrong_call_target_rejected(self):
        image = fx.pe_image(link_addresses={fx.CALLEE: fx.LAYOUT[fx.OTHER_CALLEE]})
        report = run(**fx.inputs(image=image))
        self.assertRejected(report, 'relocation-target-mismatch', fx.CALLEE)
        self.assertIn('REL32 at +0x7', report['detail'])

    def test_wrong_data_target_rejected(self):
        image = fx.pe_image(link_addresses={fx.BASE: fx.LAYOUT[fx.BASE] + 4})
        report = run(**fx.inputs(image=image))
        self.assertRejected(report, 'relocation-target-mismatch', fx.BASE)
        self.assertIn('+0xd', report['detail'])

    def test_wrong_symbol_map_rva_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols'][fx.COUNTER]['rva'] += 8
        self.assertRejected(compare(**args), 'relocation-target-mismatch', fx.COUNTER)

    def test_unmapped_reference_rejected(self):
        args = fx.inputs()
        del args['symbol_map']['symbols'][fx.BASE]
        self.assertRejected(compare(**args), 'unresolved-symbol', fx.BASE)

    def test_truncated_function_rejected(self):
        # Candidate stops one byte early (no `ret`); the task still pins the full target range.
        obj = fx.coff_object(code=fx.CODE[:-1])
        self.assertRejected(run(**fx.inputs(obj=obj)), 'function-size-mismatch')

    def test_task_range_larger_than_candidate_rejected(self):
        args = fx.inputs()
        args['task']['size'] += 1
        self.assertRejected(compare(**args), 'function-size-mismatch')

    def test_target_range_past_raw_data_rejected(self):
        self.assertRejected(run(**fx.inputs(image=fx.pe_image(text_raw_size=0x20))), 'target-range-truncated')

    def test_truncated_object_file_rejected(self):
        obj = fx.coff_object()[:-6]
        self.assertRejected(run(**fx.inputs(obj=obj)), 'truncated-input')

    def test_wrong_image_rejected(self):
        args = fx.inputs()
        args['image_bytes'] = fx.pe_image(patch={0: 0x90})
        self.assertRejected(compare(**args), 'image-hash-mismatch')

    def test_manifest_disagreement_rejected(self):
        args = fx.inputs()
        args['manifest']['image_sha256'] = '0' * 64
        self.assertRejected(compare(**args), 'manifest-mismatch')
        args = fx.inputs()
        args['manifest']['status'] = 'unselected'
        self.assertRejected(compare(**args), 'target-unpinned')

    def test_stale_source_revision_rejected(self):
        args = fx.inputs()
        args['build_record']['source_revision'] = fx.sha256(b'older revision')[:40]
        self.assertRejected(compare(**args), 'stale-source-revision')

    def test_stale_recipe_rejected(self):
        args = fx.inputs()
        args['recipe_bytes'] = fx.recipe(flags=('/O1', '/Gy'))
        self.assertRejected(compare(**args), 'stale-recipe', 'recipe file')
        args = fx.inputs()
        args['build_record']['recipe_sha256'] = fx.sha256(b'other recipe')
        self.assertRejected(compare(**args), 'stale-recipe', 'built with a different recipe')

    def test_object_not_from_build_record_rejected(self):
        args = fx.inputs()
        args['object_bytes'] = fx.coff_object(code=fx.CODE[:3] + b'\x30' + fx.CODE[4:])
        self.assertRejected(compare(**args), 'object-provenance-mismatch')

    def test_unsupported_relocation_rejected(self):
        relocs = ((0x07, fx.CALLEE, fx.REL32), (0x0D, fx.BASE, fx.SECREL), (0x13, fx.COUNTER, fx.REL32_1))
        report = run(**fx.inputs(obj=fx.coff_object(relocs=relocs)))
        self.assertRejected(report, 'unsupported-relocation', 'SECREL')

    def test_omitted_exception_coverage_rejected(self):
        report = run(**fx.inputs(obj=fx.coff_object(unwind=False)))
        self.assertRejected(report, 'unwind-coverage-missing')

    def test_extra_candidate_unwind_rejected(self):
        report = run(**fx.inputs(image=fx.pe_image(pdata=False)))
        self.assertRejected(report, 'unwind-coverage-extra')

    def test_unwind_info_difference_rejected(self):
        # Same span, but the target records a 0x38-byte allocation.
        report = run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0104010004620000'))))
        self.assertRejected(report, 'unwind-info-mismatch')

    def test_handler_only_in_target_rejected(self):
        # UNW_FLAG_EHANDLER set in the target only: the unwind headers already differ.
        report = run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0904010004420000'))))
        self.assertRejected(report, 'unwind-info-mismatch')

    def test_undeclared_alias_rejected_and_declared_fold_reported(self):
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticFolded'] = {'rva': fx.LAYOUT[fx.FUNCTION], 'size': None}
        self.assertRejected(compare(**args), 'undeclared-alias')
        args['symbol_map']['symbols'][fx.FUNCTION] = {'rva': fx.LAYOUT[fx.FUNCTION], 'size': len(fx.CODE)}
        args['symbol_map']['folds'] = [[fx.FUNCTION, 'SyntheticFolded']]
        report = compare(**args)
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['coverage']['aliases_declared'], ['SyntheticFolded'])

    def test_overlapping_function_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticNeighbor'] = {'rva': fx.LAYOUT[fx.FUNCTION] + 0x10, 'size': 8}
        self.assertRejected(compare(**args), 'overlapping-function')
        args = fx.inputs()
        args['symbol_map']['symbols']['SyntheticBefore'] = {'rva': fx.LAYOUT[fx.FUNCTION] - 4, 'size': 8}
        self.assertRejected(compare(**args), 'overlapping-function')

    def test_symbol_map_conflict_and_wrong_build_rejected(self):
        args = fx.inputs()
        args['symbol_map']['symbols'][fx.FUNCTION] = {'rva': 0x1020, 'size': None}
        self.assertRejected(compare(**args), 'symbol-map-conflict')
        args = fx.inputs()
        args['symbol_map']['build_id'] = 'another-build'
        self.assertRejected(compare(**args), 'symbol-map-build-mismatch')

    def test_reports_contain_no_code_bytes(self):
        image = fx.pe_image()
        linked = image[0x400 + 0x10:0x400 + 0x10 + len(fx.CODE)]
        windows = {blob[i:i + 4].hex() for blob in (fx.CODE, linked, fx.XDATA) for i in range(len(blob) - 3)}
        reports = [run(), run(**fx.inputs(image=fx.pe_image(patch={3: 0x38}))),
                   run(**fx.inputs(image=fx.pe_image(link_addresses={fx.CALLEE: 0x1008}))),
                   run(**fx.inputs(image=fx.pe_image(xdata=bytes.fromhex('0104010004620000'))))]
        for report in reports:
            text = json.dumps(report).lower()
            leaks = [w for w in windows if w in text]
            self.assertEqual(leaks, [], report['reason'])
            self.assertNotIn('"raw"', text)

    def test_sanitizer_refuses_hex_and_bytes(self):
        with self.assertRaisesRegex(ValueError, 'hex run'):
            sanitized({'detail': 'differs: 4883ec288b09e800'})
        with self.assertRaisesRegex(ValueError, 'raw bytes'):
            sanitized({'detail': b'\x48\x83'})
        sanitized({'image_sha256': 'a' * 64})

    def test_diagnostics_only_under_private_root(self):
        with tempfile.TemporaryDirectory() as folder:
            private = Path(folder) / 'private'
            path = private / 'compare' / 'synthetic-sum.json'
            report = run(**fx.inputs(image=fx.pe_image(patch={3: 0x38})), diagnostics=path, private_root=private)
            self.assertEqual(report['reason'], 'code-byte-mismatch')
            raw = json.loads(path.read_text())['raw']
            self.assertIn('38', raw['target'])
            with self.assertRaises(Reject) as caught:
                run(diagnostics=Path(folder) / 'public.json', private_root=private)
            self.assertEqual(caught.exception.reason, 'diagnostics-path-not-private')
            self.assertFalse((Path(folder) / 'public.json').exists())

    def test_cli_exit_codes_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for label, args in (('pass', fx.inputs()), ('fail', fx.inputs(image=fx.pe_image(patch={3: 0x38})))):
                paths = {}
                for key, name in (('task', 'task.json'), ('manifest', 'manifest.json'),
                                  ('build_record', 'build.json'), ('symbol_map', 'symbols.json')):
                    paths[key] = root / f'{label}-{name}'
                    paths[key].write_text(json.dumps(args[key]))
                for key, name in (('recipe_bytes', 'recipe.json'), ('object_bytes', 'candidate.coff'),
                                  ('image_bytes', 'target.pe')):
                    paths[key] = root / f'{label}-{name}'
                    paths[key].write_bytes(args[key])
                out = root / f'{label}-report.json'
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'tools/compare.py'), '--task', paths['task'],
                     '--manifest', paths['manifest'], '--recipe', paths['recipe_bytes'],
                     '--build-record', paths['build_record'], '--object', paths['object_bytes'],
                     '--image', paths['image_bytes'], '--symbols', paths['symbol_map'], '--report', out],
                    capture_output=True, text=True)
                report = json.loads(out.read_text())
                self.assertEqual(result.returncode, 0 if label == 'pass' else 1, result.stderr)
                self.assertEqual(report['result'], label)



def patched(unit, symbol, offset, blob, **link_args):
    """An image linked from `unit` with `blob` written at `symbol + offset`."""
    return unit.link(fx.image_externals(), patches={fx.section_rva(unit, symbol) + offset: blob}, **link_args)


class ExceptionDataTests(unittest.TestCase):
    """Contract v2: handlers, handler data, funclets, chained unwind info and jump tables."""

    def assertRejected(self, report, reason, detail=None):
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['reason'], reason, report['detail'])
        if detail:
            self.assertIn(detail, report['detail'])

    def catch(self, unit=None, **link_args):
        return compare(**fx.catch_inputs(unit, **link_args))

    def catch_image(self, image, unit=None, extra_map=None):
        unit = unit or fx.catch_unit()
        extra = dict(fx.catch_map(unit), **(extra_map or {}))
        return compare(**fx.unit_inputs(unit, fx.CATCH_FUNCTION, fx.image_externals(), image=image, extra_map=extra))

    def chain(self, unit=None, image=None):
        unit = unit or fx.chain_unit()
        return compare(**fx.unit_inputs(unit, fx.CHAIN_FUNCTION, fx.image_externals(), image=image))

    def seh(self, unit=None, image=None):
        unit = unit or fx.seh_unit()
        return compare(**fx.unit_inputs(unit, fx.SEH_FUNCTION, fx.image_externals(), image=image))

    # -- positive cases -----------------------------------------------------------------------

    def test_cxx_try_catch_with_funclets_passes(self):
        report = self.catch()
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual((cov['code_bytes_exact'] + cov['code_bytes_by_reference'], cov['code_bytes_total']),
                         (len(fx.CATCH_CODE), len(fx.CATCH_CODE)))
        self.assertEqual((cov['funclet_sections'], cov['funclet_bytes_total']), (1, len(fx.FUNCLET_CODE)))
        self.assertEqual(cov['funclet_bytes_exact'] + cov['funclet_bytes_by_reference'], len(fx.FUNCLET_CODE))
        self.assertEqual(cov['unwind_entries'], 2)
        self.assertEqual(cov['eh']['handlers'], {'__CxxFrameHandler3': 2})
        self.assertEqual(cov['eh']['structures'], {'funcinfo': 1, 'unwind_map_entry': 2, 'try_block': 1,
                                                   'handler_type': 2, 'ip_to_state': 4})
        self.assertEqual(cov['eh']['type_names_compared'], 1)
        self.assertEqual(report['contract_version'], 2)

    def test_chained_unwind_passes_over_whole_section(self):
        report = self.chain()
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual((cov['unwind_entries'], cov['unwind_chained_entries'], cov['unwind']), (3, 2, 'covered'))
        self.assertEqual(cov['code_bytes_total'], len(fx.CHAIN_CODE))

    def test_seh_scope_table_with_filter_funclet_passes(self):
        report = self.seh()
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual(cov['eh']['structures'], {'scope_table': 1, 'scope_entry': 2})
        self.assertEqual((cov['funclet_sections'], cov['unwind_entries']), (1, 2))

    def test_gs_handlers_pass(self):
        for handler, gs in (('__GSHandlerCheck_SEH', fx.dwords(0x65, 0x10, 0x20)),
                            ('__GSHandlerCheck_SEH', fx.dwords(0x61))):
            report = self.seh(fx.seh_unit(handler, gs))
            self.assertEqual(report['result'], 'pass', report['detail'])
            self.assertEqual(report['coverage']['eh']['structures']['gs_data'], 1)

    def test_jump_table_passes_with_each_entry_checked(self):
        report = compare(**fx.unit_inputs(fx.switch_unit(), fx.SWITCH_FUNCTION, fx.image_externals()))
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['coverage']['self_rva_fields'], 4)
        self.assertEqual(report['coverage']['relocations_by_type'], {'REL32': 1, 'ADDR32NB': 4})

    # -- handler and handler data -------------------------------------------------------------

    def test_wrong_handler_rejected(self):
        image = fx.catch_unit().link(fx.image_externals(__CxxFrameHandler3=fx.OTHER_THUNK))
        self.assertRejected(self.catch_image(image), 'eh-handler-mismatch', '__CxxFrameHandler3')

    def test_unsupported_handler_rejected(self):
        self.assertRejected(self.catch(fx.catch_unit(handler='__CxxFrameHandler4')), 'unsupported-eh-handler',
                            '__CxxFrameHandler4')

    def test_other_funcinfo_magic_rejected(self):
        self.assertRejected(self.catch(fx.catch_unit(magic=0x19930520)), 'eh-funcinfo-unsupported')

    def test_altered_ip_to_state_rejected(self):
        unit = fx.catch_unit()
        image = patched(unit, '$ip2state$SyntheticCatch', 12, fx.dwords(1))
        self.assertRejected(self.catch_image(image, unit), 'eh-data-mismatch', 'ip_to_state_map[1].state')

    def test_altered_ip_boundary_rejected(self):
        unit = fx.catch_unit()
        target = fx.section_rva(unit, fx.CATCH_FUNCTION) + 5
        image = patched(unit, '$ip2state$SyntheticCatch', 8, fx.dwords(target))
        self.assertRejected(self.catch_image(image, unit), 'eh-reference-mismatch', 'ip_to_state_map[1].ip')

    def test_wrong_catch_type_rejected(self):
        # The map sends the type descriptor elsewhere: the handler's reference no longer agrees.
        unit = fx.catch_unit()
        moved = {fx.CATCH_TYPE: {'rva': fx.section_rva(unit, fx.CATCH_TYPE) + 0x40, 'size': None}}
        self.assertRejected(self.catch_image(unit.link(fx.image_externals()), unit, moved), 'eh-reference-mismatch',
                            'type_descriptor')
        # Same address, but the target's descriptor names another type.
        image = patched(unit, fx.CATCH_TYPE, 20, b'X')
        self.assertRejected(self.catch_image(image, unit), 'eh-catch-type-mismatch')

    def test_try_range_change_rejected(self):
        unit = fx.catch_unit()
        image = patched(unit, '$tryMap$SyntheticCatch', 8, fx.dwords(2))
        self.assertRejected(self.catch_image(image, unit), 'eh-data-mismatch', 'catch_high')

    def test_unaccounted_handler_data_rejected(self):
        self.assertRejected(self.catch(fx.catch_unit(handler_map_tail=fx.dwords(0))), 'eh-data-unaccounted')

    def test_unrelocated_reference_rejected(self):
        self.assertRejected(self.catch(fx.catch_unit(unrelocated_action=True)), 'eh-unrelocated-reference')

    def test_code_field_pointing_at_data_rejected(self):
        self.assertRejected(self.catch(fx.catch_unit(action_to_data=True)), 'eh-reference-kind')

    def test_scope_constant_change_rejected(self):
        unit = fx.seh_unit()
        image = patched(unit, '$unwind$SyntheticGuarded', 0x28, fx.dwords(0))
        self.assertRejected(self.seh(unit, image), 'eh-data-mismatch', 'scope table[1].handler')

    def test_gs_cookie_change_rejected(self):
        unit = fx.seh_unit('__GSHandlerCheck_SEH', fx.dwords(0x61))
        image = patched(unit, '$unwind$SyntheticGuarded', 0x30, fx.dwords(0x69))
        self.assertRejected(self.seh(unit, image), 'eh-data-mismatch', 'cookie_offset')

    # -- funclets -----------------------------------------------------------------------------

    def test_missing_funclet_action_rejected(self):
        unit = fx.catch_unit()
        image = patched(unit, '$stateUnwindMap$SyntheticCatch', 4, fx.dwords(0))
        self.assertRejected(self.catch_image(image, unit), 'eh-reference-mismatch', 'unwind_map[0].action')

    def test_missing_funclet_unwind_entry_rejected(self):
        unit = fx.catch_unit()
        funclet = fx.section_rva(unit, '?catch$0@?0??SyntheticCatch@@4HA')
        self.assertRejected(self.catch(unit, drop_pdata=(funclet,)), 'unwind-coverage-extra')

    def test_funclet_byte_change_rejected(self):
        unit = fx.catch_unit()
        image = patched(unit, '?catch$0@?0??SyntheticCatch@@4HA', 9, b'\x30')
        self.assertRejected(self.catch_image(image, unit), 'code-byte-mismatch', 'funclet code differs at +0x9')

    def test_funclet_reference_rejected(self):
        unit = fx.catch_unit()
        image = unit.link(fx.image_externals(gSyntheticBase=0x3108))
        self.assertRejected(self.catch_image(image, unit), 'relocation-target-mismatch', fx.BASE)

    def test_funclet_overlapping_function_rejected(self):
        unit = fx.catch_unit()
        placement = unit.default_placement()
        # Only the unwind funclet (no .pdata of its own) reaches into the function's first bytes.
        placement[2] = placement[1] - 0x28
        image = unit.link(fx.image_externals(), placement)
        args = fx.unit_inputs(unit, fx.CATCH_FUNCTION, fx.image_externals(), image=image, extra_map=fx.catch_map(unit))
        self.assertRejected(compare(**args), 'eh-funclet-overlap')

    def test_map_entry_inside_funclet_rejected(self):
        unit = fx.catch_unit()
        inside = {'SyntheticNeighbor': {'rva': fx.section_rva(unit, '?catch$0@?0??SyntheticCatch@@4HA') + 4,
                                        'size': None}}
        self.assertRejected(self.catch_image(unit.link(fx.image_externals()), unit, inside), 'overlapping-function')

    # -- chained unwind and .pdata coverage ---------------------------------------------------

    def test_wrong_chained_parent_rejected(self):
        image = fx.chain_unit(second_parent='chain0').link(fx.image_externals())
        self.assertRejected(self.chain(image=image), 'unwind-chain-mismatch', 'chained begin')

    def test_uncovered_pdata_entry_rejected(self):
        unit = fx.chain_unit()
        image = unit.link(fx.image_externals())
        candidate = fx.chain_unit()
        candidate.sections = [s for s in candidate.sections
                              if not (s[0] == '.pdata' and struct.unpack_from('<I', s[1], 0)[0] == 0x20)]
        args = fx.unit_inputs(candidate, fx.CHAIN_FUNCTION, fx.image_externals(), image=image)
        self.assertRejected(compare(**args), 'unwind-coverage-missing')

    def test_overlapping_target_pdata_rejected(self):
        unit = fx.chain_unit()
        start = fx.section_rva(unit, fx.CHAIN_FUNCTION)
        unwind = fx.section_rva(unit, '$chain$1$SyntheticChain')
        extra = ((start + 0x28, start + 0x30, unwind),)
        self.assertRejected(self.chain(unit, unit.link(fx.image_externals(), extra_pdata=extra)),
                            'unwind-entry-overlap')

    def test_primary_entry_size_rejected(self):
        # An inventory that sizes a chained function by its primary .pdata entry alone.
        args = fx.unit_inputs(fx.chain_unit(), fx.CHAIN_FUNCTION, fx.image_externals())
        args['task']['size'] = 8
        self.assertRejected(compare(**args), 'function-size-mismatch')

    def test_unwind_version_two_rejected(self):
        unit = fx.chain_unit()
        unit.sections[1][1][0] = 0x02
        self.assertRejected(self.chain(unit), 'unsupported-unwind', 'version 2')

    # -- jump tables --------------------------------------------------------------------------

    def test_wrong_jump_table_entry_rejected(self):
        unit = fx.switch_unit()
        case2 = fx.section_rva(unit, fx.SWITCH_FUNCTION) + 0x2B
        image = patched(unit, fx.SWITCH_FUNCTION, fx.SWITCH_TABLE + 4, fx.dwords(case2))
        report = compare(**fx.unit_inputs(unit, fx.SWITCH_FUNCTION, fx.image_externals(), image=image))
        self.assertRejected(report, 'relocation-target-mismatch', 'ADDR32NB at +0x38')

    def test_image_base_map_conflict_rejected(self):
        args = fx.unit_inputs(fx.switch_unit(), fx.SWITCH_FUNCTION, fx.image_externals(),
                              extra_map={'__ImageBase': {'rva': 0x1000, 'size': None}})
        self.assertRejected(compare(**args), 'symbol-map-conflict', '__ImageBase')

    # -- code section hash --------------------------------------------------------------------

    def code_hash(self, unit, stamp=0):
        obj = bytearray(unit.coff())
        struct.pack_into('<I', obj, 4, stamp)
        args = fx.unit_inputs(unit, fx.SWITCH_FUNCTION, fx.image_externals(), image=fx.switch_unit().link(
            fx.image_externals()))
        args['object_bytes'] = bytes(obj)
        args['build_record']['object_sha256'] = fx.sha256(bytes(obj))
        report = compare(**args)
        return report, report['candidate']['code_section_sha256']

    def test_code_section_hash_ignores_stamp_symbol_order_and_other_sections(self):
        report, base = self.code_hash(fx.switch_unit())
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['candidate']['code_sections'], 1)
        other = fx.switch_unit()
        other.symbols.reverse()
        other.section('.rdata', b'unrelated constant\0', fx.SCN_XDATA)
        report, varied = self.code_hash(other, stamp=0x5F5E100)
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertNotEqual(fx.switch_unit().coff(), other.coff())
        self.assertEqual(varied, base)

    def test_code_section_hash_follows_code_and_references(self):
        _, base = self.code_hash(fx.switch_unit())
        changed = fx.switch_unit()
        changed.sections[0][1][0x1F + 1] = 0x07
        self.assertNotEqual(self.code_hash(changed)[1], base)
        retargeted = fx.switch_unit()
        rels = retargeted.sections[0][2]
        rels[rels.index((fx.SWITCH_TABLE, '$LN2', fx.ADDR32NB))] = (fx.SWITCH_TABLE, '$LN3', fx.ADDR32NB)
        self.assertNotEqual(self.code_hash(retargeted)[1], base)

    def test_code_section_hash_covers_funclets(self):
        report = self.catch()
        self.assertEqual(report['candidate']['code_sections'], 2)
        unit = fx.catch_unit()
        unit.sections[1][1][0x20] = 0x90    # funclet padding byte; the image is linked from the original
        args = fx.unit_inputs(unit, fx.CATCH_FUNCTION, fx.image_externals(), image=fx.catch_unit().link(
            fx.image_externals()), extra_map=fx.catch_map(unit))
        self.assertNotEqual(compare(**args)['candidate']['code_section_sha256'],
                            report['candidate']['code_section_sha256'])

    # -- reports ------------------------------------------------------------------------------

    def test_v2_reports_contain_no_bytes(self):
        unit = fx.catch_unit()
        blobs = [fx.CATCH_CODE, fx.FUNCLET_CODE, fx.TYPE_DESCRIPTOR] + [bytes(s[1]) for s in unit.sections]
        windows = {b[i:i + 4].hex() for b in blobs for i in range(len(b) - 3)} - {'00000000', 'ffffffff'}
        reports = [self.catch(), self.catch_image(patched(unit, fx.CATCH_TYPE, 20, b'X'), unit),
                   self.catch_image(patched(unit, '?catch$0@?0??SyntheticCatch@@4HA', 9, b'\x30'), unit),
                   self.catch_image(patched(unit, '$ip2state$SyntheticCatch', 12, fx.dwords(1)), unit)]
        for report in reports:
            text = json.dumps(report).lower()
            self.assertEqual([w for w in windows if w in text], [], report['reason'])
            self.assertNotIn('SyntheticError', json.dumps(report))


if __name__ == '__main__':
    unittest.main()
