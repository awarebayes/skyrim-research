"""Comparator contract v2: positive cases and a rejection test for each failure it must catch."""
import hashlib
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

    def test_map_bytes_are_hashed_into_the_report(self):
        args = fx.inputs()
        blob = json.dumps(args['symbol_map']).encode()
        report = compare(**dict(args, symbol_map=blob))
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['symbol_map_sha256'], hashlib.sha256(blob).hexdigest())
        # A parsed map leaves no hash, so such a report cannot back a match record.
        self.assertNotIn('symbol_map_sha256', compare(**args))

    def test_map_bytes_not_json_rejected_with_hash(self):
        report = compare(**dict(fx.inputs(), symbol_map=b'{not json'))
        self.assertRejected(report, 'invalid-symbol-map')
        self.assertEqual(report['symbol_map_sha256'], hashlib.sha256(b'{not json').hexdigest())

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
        self.assertEqual(report['comparator']['version'], '0.6.0')
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

    def test_funclet_ranges_are_reported(self):
        report = self.catch()
        self.assertEqual(report['result'], 'pass', report['detail'])
        [(start, length)] = report['coverage']['funclet_ranges']
        self.assertEqual(length, len(fx.FUNCLET_CODE))
        # The exact start, not only containment: a shifted range would still pass the overlap probe.
        self.assertEqual(start, fx.section_rva(fx.catch_unit(), '?catch$0@?0??SyntheticCatch@@4HA'))
        fn = report['function']
        self.assertTrue(start >= fn['rva'] + fn['size'] or start + length <= fn['rva'])
        # A map entry inside that range is what the comparator rejects, so the range is the one recorded.
        args = fx.catch_inputs()
        args['symbol_map']['symbols']['Inside'] = {'rva': start + 1, 'size': None}
        bad = compare(**args)
        self.assertRejected(bad, 'overlapping-function', 'overlaps a funclet')

    def test_no_funclet_ranges_without_funclets(self):
        self.assertEqual(self.chain()['coverage']['funclet_ranges'], [])

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

    # -- review probes against 0.2.0 -----------------------------------------------------------

    def test_es_type_list_against_external_symbol_rejected(self):
        # Mapped and linked consistently: only the rule that data references bind locally catches it.
        unit = fx.catch_unit(external_es_types='gSyntheticElsewhere')
        externals = fx.image_externals(gSyntheticElsewhere=0x3200)
        args = fx.unit_inputs(unit, fx.CATCH_FUNCTION, externals, extra_map=fx.catch_map(unit))
        self.assertRejected(compare(**args), 'eh-reference-not-local', 'es_type_list')

    def test_unwind_action_against_external_symbol_rejected(self):
        unit = fx.catch_unit(external_action='SyntheticOtherDtor')
        externals = fx.image_externals(SyntheticOtherDtor=fx.OTHER_THUNK)
        args = fx.unit_inputs(unit, fx.CATCH_FUNCTION, externals, extra_map=fx.catch_map(unit))
        self.assertRejected(compare(**args), 'eh-reference-not-local', 'unwind_map[0].action')

    def test_candidate_cut_at_chained_boundary_rejected(self):
        # The target function has three entries; the candidate stops after the first chained one.
        image = fx.chain_unit().link(fx.image_externals())
        report = self.chain(fx.chain_unit(entries=2), image)
        self.assertRejected(report, 'unwind-chain-outside')

    def test_funclet_entry_outside_compared_code_rejected(self):
        unit = fx.catch_unit()
        funclet_unwind = fx.section_rva(unit, '$unwind$?catch$0@?0??SyntheticCatch@@4HA')
        extra = ((0x1F00, 0x1F10, funclet_unwind),)
        self.assertRejected(self.catch(unit, extra_pdata=extra), 'eh-funclet-outside')

    def test_truncated_funclet_without_pdata_rejected(self):
        # Drop the unwind funclet's final jmp from the candidate; the target keeps it.
        image = fx.catch_unit().link(fx.image_externals())
        unit = fx.catch_unit()
        unit.sections[1][1] = bytearray(fx.FUNCLET_CODE[:0x28])
        unit.sections[1][2] = [r for r in unit.sections[1][2] if r[0] != 0x29]
        self.assertRejected(self.catch_image(image, unit), 'eh-funclet-extent')

    def truncated_dtor(self, **unit_args):
        """The unwind funclet dtor$0 cut 7 bytes in, before its final jmp; the target keeps it."""
        unit = fx.catch_unit(**unit_args)
        unit.sections[1][1] = bytearray(fx.FUNCLET_CODE[:0x28])
        unit.sections[1][2] = [r for r in unit.sections[1][2] if r[0] != 0x29]
        return unit

    # -- review probes against 0.3.0 -----------------------------------------------------------

    def test_truncated_funclet_excused_by_own_ip_entry_rejected(self):
        # Target and candidate both have an IP-to-state entry at dtor$0+7; in the candidate that
        # address is one past its own section, which must not count as a boundary the target shows.
        image = fx.catch_unit(last_ip_in_dtor=7).link(fx.image_externals())
        unit = self.truncated_dtor(last_ip_in_dtor=7)
        self.assertRejected(self.catch_image(image, unit), 'eh-funclet-extent')

    def test_truncated_funclet_excused_by_map_entry_rejected(self):
        # A map entry placed at the cut names nothing the target shows there.
        image = fx.catch_unit().link(fx.image_externals())
        unit = self.truncated_dtor()
        cut = fx.section_rva(fx.catch_unit(), '?dtor$0@?0??SyntheticCatch@@4HA') + 7
        self.assertRejected(self.catch_image(image, unit, extra_map={'SyntheticAtCut': {'rva': cut, 'size': None}}),
                            'eh-funclet-extent')

    def test_ip_entry_inside_funclet_passes_when_whole(self):
        # The same IP-to-state entry with the whole funclet in the candidate is a valid layout.
        image = fx.catch_unit(last_ip_in_dtor=7).link(fx.image_externals())
        self.assertEqual(self.catch_image(image, fx.catch_unit(last_ip_in_dtor=7))['result'], 'pass')

    def test_funclet_end_inside_padding_passes(self):
        # The catch_unit funclet section ends mid-line; the linker's int3 fill is a boundary.
        self.assertEqual(self.catch()['result'], 'pass')

    def test_code_section_hash_tells_same_named_targets_apart(self):
        from compare import code_section_sha256
        from pecoff import CoffObject

        def variant(first, second):
            u = fx.Unit()
            f = u.section('.text$mn', bytes.fromhex('8b0500000000c3'), fx.SCN_TEXT)
            u.define('SyntheticLoad', f, storage=fx.STORAGE_EXTERNAL, function=True)
            sections = {'A': u.section('.rdata', b'A' * 8, fx.SCN_XDATA), 'B': u.section('.rdata', b'B' * 8, fx.SCN_XDATA)}
            u.define('.rdata', sections[first])
            u.define('.rdata', sections[second])     # the relocation below names the last one
            u.reloc(f, 2, '.rdata', fx.REL32)
            obj = CoffObject(u.coff())
            return code_section_sha256(obj, [obj.section(f)])

        self.assertEqual(variant('A', 'B'), variant('A', 'B'))
        self.assertNotEqual(variant('A', 'B'), variant('B', 'A'))

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


# -- packed funclets (comparator 0.6.0) -------------------------------------------------------
#
# Each case returns comparator inputs and the reason the comparator must give. The cases are a
# table so the mutation test below can run all of them against altered comparator source.

LEAF, NEIGHBOR, FRAME = fx.LEAF_FUNCLET, fx.NEIGHBOR_FUNCLET, fx.FRAME_FUNCLET
FRAME_PDATA = (0, len(FRAME), fx.FRAME_FUNCLET_UNWIND)
BAD_MAGIC = 0x19930521


def packed_case(candidate=None, image_unit=None, image=None, **image_args):
    candidate = candidate or fx.packed_unit(neighbor=False)
    if image is None:
        image = fx.packed_image(image_unit or fx.packed_unit(), **image_args)
    return fx.packed_inputs(candidate, image)


def swallowing_candidate():
    """A candidate funclet that also holds the neighbour's funclet, byte for byte."""
    unit = fx.packed_unit(neighbor=False, funclet_code=LEAF + NEIGHBOR)
    unit.reloc(unit.packed_funclet, 8, fx.CALLEE, fx.REL32)
    return unit


def merged_pdata_image():
    """The frame funclet covered by two target .pdata entries instead of one."""
    unit = fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA, neighbor_magic=BAD_MAGIC)
    at = fx.PACKED_FUNCLET_AT
    unwind = fx.section_rva(unit, f'$unwind$?dtor$0@?0??{fx.PACKED_FUNCTION}@@4HA')
    extra = ((at, at + 9, unwind), (at + 9, at + len(FRAME), unwind))
    return fx.packed_image(unit, drop_pdata=(at,), extra_pdata=extra)


PACKED_CASES = {
    # Positive: the neighbour's FuncInfo names the address right after the funclet.
    'leaf funclet ends at a neighbour funclet entry': (lambda: packed_case(), 'all-checks-passed'),
    # Positive: the funclet's own .pdata entry ends where the candidate section ends; nothing
    # after it is declared (the neighbour's FuncInfo is not readable as one).
    'frame funclet ends at its own pdata end': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME, funclet_pdata=FRAME_PDATA),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA, neighbor_magic=BAD_MAGIC)),
        'all-checks-passed'),
    # The same bytes after the funclet, but no metadata declares them: nothing proves the end.
    'neighbour code without metadata': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor=False),
                            patches={fx.PACKED_FUNCLET_AT + len(LEAF): NEIGHBOR}),
        'eh-funclet-extent'),
    'candidate one byte shorter': (
        lambda: packed_case(image_unit=fx.packed_unit(funclet_code=LEAF + b'\x90')), 'eh-funclet-extent'),
    # One byte longer, equal to the neighbour's first byte, so only the extent rules can catch it.
    'candidate one byte longer': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=LEAF + NEIGHBOR[:1])),
        'eh-funclet-entry-inside'),
    # The candidate claims the neighbour's whole funclet; int3 padding follows it in the image.
    'candidate swallows the neighbour funclet': (lambda: packed_case(swallowing_candidate()),
                                                 'eh-funclet-entry-inside'),
    'byte differs inside the funclet': (
        lambda: packed_case(patches={fx.PACKED_FUNCLET_AT + 3: b'\x31'}), 'code-byte-mismatch'),
    # The neighbour's unwind map names an address 4 bytes into its funclet, not the boundary.
    'neighbour action elsewhere': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_action_addend=4)), 'eh-funclet-extent'),
    # Only an IP-to-state entry of the neighbour points at the boundary; that is no funclet entry.
    'neighbour ip-to-state entry only': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_action_addend=4, neighbor_ip_into_funclet=0)),
        'eh-funclet-extent'),
    # The neighbour's handler is not one this function's compared unwind info names.
    'neighbour under another handler': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_handler='__GSHandlerCheck_EH')),
        'eh-funclet-extent'),
    'neighbour funcinfo magic wrong': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_magic=BAD_MAGIC)), 'eh-funclet-extent'),
    # The compared parent's own unwind map sends the action 4 bytes further in the target.
    'own unwind action elsewhere': (
        lambda: packed_case(image_unit=fx.packed_unit(action_addend=4)), 'code-byte-mismatch'),
    'frame funclet: candidate one byte shorter': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME[:-1],
                                           funclet_pdata=(0, len(FRAME) - 1, fx.FRAME_FUNCLET_UNWIND)),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA)),
        'unwind-entry-crosses-boundary'),
    'frame funclet: candidate one byte longer': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME + NEIGHBOR[:1],
                                           funclet_pdata=FRAME_PDATA),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA)),
        'eh-funclet-entry-inside'),
    'frame funclet: candidate lacks the pdata entry': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA)),
        'unwind-coverage-missing'),
    'frame funclet: target splits the pdata entry': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME, funclet_pdata=FRAME_PDATA),
                            image=merged_pdata_image()),
        'unwind-coverage-missing'),
    # Both sides' .pdata entry stops one byte before the section end and nothing starts there.
    'frame funclet: pdata ends short of the section': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME,
                                           funclet_pdata=(0, len(FRAME) - 1, fx.FRAME_FUNCLET_UNWIND)),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=(0, len(FRAME) - 1,
                                                                              fx.FRAME_FUNCLET_UNWIND),
                                           neighbor_magic=BAD_MAGIC)),
        'eh-funclet-past-pdata'),
    # A frame funclet, then a leaf funclet of the same FuncInfo in the same section: the .pdata
    # end inside the section is fine, but it is not the section end, and nothing follows it.
    'frame funclet then own leaf, nothing after': (lambda: frame_then_leaf_case(), 'eh-funclet-extent'),
    # The guard sees FuncInfos under every handler, not only this function's: the neighbour
    # swallowed here is reached through __GSHandlerCheck_EH, which the compared function never names.
    'candidate swallows a neighbour under another handler': (
        lambda: packed_case(swallowing_candidate(), fx.packed_unit(neighbor_handler='__GSHandlerCheck_EH')),
        'eh-funclet-entry-inside'),
    # Positive: only the neighbour's catch handler (not its unwind action) names the boundary.
    'leaf funclet ends at a neighbour catch handler': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_action_addend=4, neighbor_catch_at=0)),
        'all-checks-passed', {'funclet-entry': 1}),
    # The neighbour's unwind map names the boundary but its try map is unreadable: the whole
    # FuncInfo counts for nothing.
    'neighbour funcinfo readable only in part': (
        lambda: packed_case(image_unit=fx.packed_unit(neighbor_bad_try_map=True)), 'eh-funclet-extent'),
    # A chained unwind info that also carries handler flags, whose chained words read as the
    # handler and a FuncInfo naming the boundary: only primary unwind infos lead to FuncInfos.
    'chained unwind info read as a handler': (lambda: fake_case(chained=True), 'eh-funclet-extent'),
    'primary unwind info names the boundary': (lambda: fake_case(chained=False), 'all-checks-passed',
                                               {'funclet-entry': 1}),
    # An entry inside the funclet that this function's FuncInfo names is allowed; one that a
    # second FuncInfo names as well (a folded funclet) is refused.
    'own funclet entry inside the funclet': (
        lambda: packed_case(fx.packed_unit(neighbor=False, extra_action=7), fx.packed_unit(extra_action=7)),
        'all-checks-passed', {'funclet-entry': 1}),
    'own entry inside the funclet also named by another FuncInfo': (lambda: folded_case(), 'eh-funclet-entry-inside'),
    # x2 is bound only by the exception data of x3, compared after x1, yet x1's end is shown as
    # compared code because extents are checked once every funclet is bound.
    'funclet bound later counts as compared code': (
        lambda: fx.nested_inputs(), 'all-checks-passed', {'compared-code': 1, 'pdata-end': 1, 'int3-padding': 1}),
    # The candidate funclet also holds a whole procedure with its own unchained .pdata entry.
    'funclet absorbs a procedure with its own pdata': (lambda: absorb_case(), 'eh-funclet-absorbs-procedure'),
    # The guard keeps FuncInfos of older magics and what it could read of a damaged one.
    'candidate swallows a neighbour with an older FuncInfo magic': (
        lambda: packed_case(swallowing_candidate(), fx.packed_unit(neighbor_magic=BAD_MAGIC)),
        'eh-funclet-entry-inside'),
    'candidate swallows a neighbour whose FuncInfo is readable only in part': (
        lambda: packed_case(swallowing_candidate(), fx.packed_unit(neighbor_bad_try_map=True)),
        'eh-funclet-entry-inside'),
    # The frame funclet's .pdata entry ends, then undeclared nops run up to the neighbour's entry.
    'frame funclet goes on past its pdata end': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=FRAME + b'\x90' * 3, funclet_pdata=FRAME_PDATA),
                            fx.packed_unit(funclet_code=FRAME, funclet_pdata=FRAME_PDATA, neighbor_gap=3)),
        'eh-funclet-past-pdata'),
    # Not refusable from metadata, so a pass by design (contract): a leaf funclet ending in
    # undeclared bytes, all equal, before a declared neighbour entry.
    'leaf funclet with undeclared bytes before a neighbour entry': (
        lambda: packed_case(fx.packed_unit(neighbor=False, funclet_code=LEAF + b'\x90' * 4),
                            fx.packed_unit(neighbor_gap=4)),
        'all-checks-passed', {'funclet-entry': 1}),
}


def frame_then_leaf_case():
    def unit(neighbor):
        u = fx.packed_unit(neighbor=neighbor, funclet_code=FRAME + LEAF, funclet_pdata=FRAME_PDATA,
                           extra_action=len(FRAME), neighbor_magic=BAD_MAGIC)
        u.reloc(u.packed_funclet, 0x13, fx.CALLEE, fx.REL32)
        return u
    return packed_case(unit(False), unit(True))


def fake_case(chained):
    """Neighbour bytes after the funclet, named only by a hand-placed FuncInfo (fx.fake_funcinfo)."""
    boundary = fx.PACKED_FUNCLET_AT + len(LEAF)
    patches, extra = fx.fake_funcinfo([boundary], chained=chained)
    patches[boundary] = NEIGHBOR
    return packed_case(image_unit=fx.packed_unit(neighbor=False), patches=patches, extra_pdata=extra)


def folded_case():
    patches, extra = fx.fake_funcinfo([fx.PACKED_FUNCLET_AT + 7])
    return packed_case(fx.packed_unit(neighbor=False, extra_action=7), fx.packed_unit(extra_action=7),
                       patches=patches, extra_pdata=extra)


def absorb_case():
    code = LEAF + FRAME
    more = ((len(LEAF), len(code), fx.FRAME_FUNCLET_UNWIND),)
    unit = fx.packed_unit(neighbor=False, funclet_code=code, more_funclet_pdata=more)
    return packed_case(unit, fx.packed_unit(neighbor=False, funclet_code=code, more_funclet_pdata=more))


def case_outcome(report, expected):
    """What a case checks: the reason, and for cases that name it, the end evidence."""
    if len(expected) > 2:
        return report['reason'], report['coverage']['funclet_end_evidence']
    return report['reason']


def case_expected(expected):
    return (expected[1], expected[2]) if len(expected) > 2 else expected[1]


class PackedFuncletTests(unittest.TestCase):
    """Funclet extent from image metadata: own .pdata end, or a funclet entry a FuncInfo names."""

    def test_cases(self):
        for label, case in PACKED_CASES.items():
            with self.subTest(label):
                report = compare(**case[0]())
                self.assertEqual(case_outcome(report, case), case_expected(case), report['detail'])
                self.assertEqual(report['result'], 'pass' if case[1] == 'all-checks-passed' else 'fail')

    def test_leaf_pass_covers_the_whole_funclet_and_names_its_evidence(self):
        report = compare(**PACKED_CASES['leaf funclet ends at a neighbour funclet entry'][0]())
        cov = report['coverage']
        self.assertEqual(cov['funclet_ranges'], [[fx.PACKED_FUNCLET_AT, len(LEAF)]])
        self.assertEqual(cov['funclet_bytes_exact'] + cov['funclet_bytes_by_reference'], len(LEAF))
        self.assertEqual(cov['funclet_end_evidence'], {'funclet-entry': 1})

    def test_frame_pass_names_pdata_end(self):
        report = compare(**PACKED_CASES['frame funclet ends at its own pdata end'][0]())
        self.assertEqual(report['coverage']['funclet_end_evidence'], {'pdata-end': 1})
        self.assertEqual(report['coverage']['unwind_entries'], 2)

    def test_packed_image_really_packs(self):
        # The fixture must place the neighbour's funclet at the candidate's end with no int3 between.
        image = fx.packed_image(fx.packed_unit())
        start = fx.PACKED_FUNCLET_AT + len(LEAF)
        from pecoff import PeImage
        pe = PeImage(image)
        self.assertEqual(pe.read(start, 7, 'x')[1], NEIGHBOR[:7])
        self.assertNotIn(start, {b for b, _e, _u in pe.runtime_functions()})
        self.assertIn(start, pe.funclet_entries({fx.HANDLER_THUNKS['__CxxFrameHandler3']}))

    def test_existing_padding_evidence_is_named(self):
        report = compare(**fx.catch_inputs())
        self.assertEqual(report['result'], 'pass', report['detail'])
        self.assertEqual(report['coverage']['funclet_end_evidence'], {'int3-padding': 1})


class PackedFuncletMutationTests(unittest.TestCase):
    """Each weakening of the extent rules lets at least one PACKED_CASES case through wrongly."""

    TOOLS = Path(__file__).resolve().parents[1] / 'tools'
    MUTATIONS = {
        'entry-inside check removed': ('compare.py', "need(not inside, 'eh-funclet-entry-inside',",
                                       "need(True, 'eh-funclet-entry-inside',"),
        'guard narrowed to own handlers': ('compare.py', 'guard = self.image.funclet_entries(None)',
                                           'guard = self.image.funclet_entries(self.funcinfo_handler_rvas)'),
        'folded entry subset weakened to intersection': (
            'compare.py', 'not guard[rva] <= self.compared_funcinfo]', 'not guard[rva] & self.compared_funcinfo]'),
        'absorb check removed': ('compare.py', "need(flags & UNW_FLAG_CHAININFO, 'eh-funclet-absorbs-procedure',",
                                 "need(True, 'eh-funclet-absorbs-procedure',"),
        'extents checked in the loop': ('compare.py', (
            ('            compared.append(sec)\n',
             '            compared.append(sec)\n            self.check_funclet_end(sec, start, start + len(sec.data))\n'),
            ('        for sec in compared:\n            start = self.bound[sec.index]\n'
             '            self.check_funclet_end(sec, start, start + len(sec.data))', '        pass'))),
        'catch handler read at the wrong offset': ('pecoff.py', 'table, 20 * c + 12)', 'table, 20 * c + 8)'),
        'evidence counts a FuncInfo in part': ('pecoff.py', '            if not lenient:\n                raise',
                                               '            pass'),
        'guard drops a FuncInfo read in part': ('pecoff.py', '            if not lenient:\n                raise',
                                                '            raise'),
        'past-pdata check removed': ('compare.py', 'need(finish == end or finish in span_starts',
                                     'need(True or finish == end or finish in span_starts'),
        'chained unwind infos read': ('pecoff.py', 'if head[0] & 0x7 != 1 or flags & UNW_FLAG_CHAININFO or not',
                                      'if head[0] & 0x7 != 1 or not'),
        'pdata end loosened': ('compare.py', 'if any(finish == end for', 'if any(finish <= end for'),
        'pdata end ignored': ('compare.py', 'if any(finish == end for', 'if False and any(finish == end for'),
        'entry rule accepts a near entry': ('compare.py', 'elif end in declared:',
                                            'elif any(abs(end - r) <= 4 for r in declared):'),
        'handler filter dropped': ('pecoff.py', 'if (key is not None and handler not in key) or funcinfo in seen:',
                                   'if funcinfo in seen:'),
        'magic check dropped': ('pecoff.py', 'if magic not in (FUNCINFO_MAGICS if lenient else (FUNCINFO_MAGIC,)):',
                                'if False:'),
        'evidence accepts older magics': ('pecoff.py',
                                          'if magic not in (FUNCINFO_MAGICS if lenient else (FUNCINFO_MAGIC,)):',
                                          'if magic not in FUNCINFO_MAGICS:'),
        'guard reads the current magic only': ('pecoff.py',
                                               'if magic not in (FUNCINFO_MAGICS if lenient else (FUNCINFO_MAGIC,)):',
                                               'if magic != FUNCINFO_MAGIC:'),
        'ip-to-state entries counted': (
            'pecoff.py', '        # A null action (a state without cleanup) names no code.',
            "        n_ip, ip_map = fields[5:7]\n"
            "        if n_ip:\n"
            "            table = self.read(ip_map, 8 * n_ip, 'ip map')[1]\n"
            "            found |= {struct.unpack_from('<I', table, 8 * i)[0] for i in range(n_ip)}"),
    }

    def load_mutant(self, filename, old, new=None):
        """`old`/`new` is one replacement, or `old` a tuple of (old, new) pairs applied in turn."""
        import importlib.util
        pairs = old if new is None else ((old, new),)
        source = (self.TOOLS / filename).read_text()
        for before, after in pairs:
            self.assertEqual(source.count(before), 1, before)
            source = source.replace(before, after)
        saved = {name: sys.modules.get(name) for name in ('pecoff', 'compare_mutant')}
        # The mutant hashes its own source into each report, so its files must outlive the load.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        try:
            for name in ('compare.py', 'pecoff.py'):
                text = (self.TOOLS / name).read_text()
                (Path(tmp.name) / name).write_text(source if name == filename else text)
            spec = importlib.util.spec_from_file_location('pecoff', Path(tmp.name) / 'pecoff.py')
            pecoff_mutant = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pecoff_mutant)
            sys.modules['pecoff'] = pecoff_mutant
            spec = importlib.util.spec_from_file_location('compare_mutant', Path(tmp.name) / 'compare.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.compare
        finally:
            for name, mod in saved.items():
                if mod is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = mod

    def wrong_cases(self, mutant):
        wrong = []
        for label, case in PACKED_CASES.items():
            try:
                got = case_outcome(mutant(**case[0]()), case)
            except Exception as exc:     # a mutant that crashes is caught as well
                got = type(exc).__name__
            if got != case_expected(case):
                wrong.append(label)
        return wrong

    def test_unmutated_source_gets_every_case_right(self):
        self.assertEqual(self.wrong_cases(self.load_mutant('compare.py', 'def u32(', 'def u32(')), [])

    def test_every_mutation_is_caught(self):
        for label, (filename, *change) in self.MUTATIONS.items():
            with self.subTest(label):
                self.assertNotEqual(self.wrong_cases(self.load_mutant(filename, *change)), [], label)


def tls_entry(offset=fx.TLS_OFFSET, size=4):
    return {'kind': 'thread-local', 'tls_offset': offset, 'size': size}


class ThreadLocalTests(unittest.TestCase):
    """Thread-local variables: SECREL against declared TLS-template offsets, _tls_index from the image."""

    def assertRejected(self, report, reason, detail=None):
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['reason'], reason, report['detail'])
        if detail:
            self.assertIn(detail, report['detail'])

    def assertPass(self, report):
        self.assertEqual(report['result'], 'pass', report['detail'])
        cov = report['coverage']
        self.assertEqual(cov['code_bytes_exact'] + cov['code_bytes_by_reference'], len(fx.TLS_CODE))
        self.assertEqual(cov['relocations_by_type'], {'REL32': 1, 'SECREL': 1})

    def linked(self, **tls):
        return fx.tls_unit().link({fx.TLS_INDEX: fx.TLS_INDEX_RVA}, tls=fx.tls_layout(**tls))

    def test_fixture_links_secrel_as_template_offset(self):
        image = self.linked()
        args = fx.tls_inputs(image=image)
        start = 0x400 + (args['task']['rva'] - 0x1000)
        self.assertEqual(struct.unpack_from('<I', image, start + 0x10)[0], fx.TLS_OFFSET)

    def test_extern_thread_local_passes(self):
        self.assertPass(compare(**fx.tls_inputs()))

    def test_variable_defined_in_tls_section_passes(self):
        self.assertPass(compare(**fx.tls_inputs(unit=fx.tls_unit(var_section='.tls$'))))

    def test_tls_index_map_entry_that_agrees_passes(self):
        self.assertPass(compare(**fx.tls_inputs(index_entry=True)))

    def test_member_addend_inside_variable_passes(self):
        unit = fx.tls_unit(addend=4)
        self.assertPass(compare(**fx.tls_inputs(unit=unit, var_entry=tls_entry(size=8))))

    def test_unsized_entry_passes(self):
        self.assertPass(compare(**fx.tls_inputs(var_entry=tls_entry(size=None))))

    def test_wrong_offset_rejected(self):
        report = compare(**fx.tls_inputs(var_entry=tls_entry(offset=fx.TLS_OFFSET + 4)))
        self.assertRejected(report, 'relocation-target-mismatch', 'SECREL at +0x10')
        self.assertIn('does not encode the offset of', report['detail'])

    def test_target_reading_another_offset_rejected(self):
        # The image reads 0x76c while the map declares 0x768: the target's displacement is not trusted.
        report = compare(**fx.tls_inputs(tls=fx.tls_layout(offset=fx.TLS_OFFSET + 4)))
        self.assertRejected(report, 'relocation-target-mismatch', 'SECREL')

    def test_offset_outside_template_rejected(self):
        report = compare(**fx.tls_inputs(var_entry=tls_entry(offset=fx.TLS_TEMPLATE_SIZE)))
        self.assertRejected(report, 'tls-offset-outside-template')
        # Starts inside, but its 4 bytes run past the end.
        report = compare(**fx.tls_inputs(var_entry=tls_entry(offset=fx.TLS_TEMPLATE_SIZE - 2)))
        self.assertRejected(report, 'tls-offset-outside-template')

    def test_offset_past_shorter_template_rejected(self):
        # Image and map agree on the field, but the directory's template ends before the variable.
        tls = fx.tls_layout(offset=0x100, size=0x100)
        report = compare(**fx.tls_inputs(tls=tls, var_entry=tls_entry(offset=0x100)))
        self.assertRejected(report, 'tls-offset-outside-template')

    def test_addend_outside_variable_rejected(self):
        report = compare(**fx.tls_inputs(unit=fx.tls_unit(addend=4)))
        self.assertRejected(report, 'tls-offset-outside-template', 'plus 4')

    def test_secrel_to_non_tls_section_rejected(self):
        for name in ('.data', '.rdata$tls', '.tlsx'):
            with self.subTest(section=name):
                report = compare(**fx.tls_inputs(unit=fx.tls_unit(var_section=name)))
                self.assertRejected(report, 'unsupported-relocation', 'not thread-local')

    def test_secrel_to_section_symbol_rejected(self):
        unit = fx.tls_unit(var_section='.tls$')
        unit.symbols.append(('.tls$', 0, 2, 0, fx.STORAGE_STATIC))
        unit.sections[0][2] = [(o, '.tls$', k) if k == fx.SECREL else (o, s, k) for o, s, k in unit.sections[0][2]]
        args = fx.tls_inputs(unit=unit, image=self.linked())
        args['symbol_map']['symbols']['.tls$'] = tls_entry()
        self.assertRejected(compare(**args), 'unsupported-relocation', 'section symbol')

    def test_secrel_to_mapped_rva_rejected(self):
        report = compare(**fx.tls_inputs(var_entry={'rva': 0x5000 + fx.TLS_OFFSET, 'size': 4}))
        self.assertRejected(report, 'unsupported-relocation', 'not thread-local')

    def test_missing_map_entry_rejected(self):
        args = fx.tls_inputs()
        del args['symbol_map']['symbols'][fx.TLS_VAR]
        self.assertRejected(compare(**args), 'unresolved-symbol', fx.TLS_VAR)

    def test_tls_index_map_entry_elsewhere_rejected(self):
        args = fx.tls_inputs(index_entry=True)
        args['symbol_map']['symbols'][fx.TLS_INDEX]['rva'] = fx.TLS_INDEX_RVA + 8
        self.assertRejected(compare(**args), 'tls-index-mismatch')

    def test_code_using_another_index_slot_rejected(self):
        # The directory names 0x3200; the target's code reads 0x3208.
        report = compare(**fx.tls_inputs(link_index=fx.TLS_INDEX_RVA + 8))
        self.assertRejected(report, 'relocation-target-mismatch', '_tls_index')
        # A map entry agreeing with the code but not with the directory does not rescue it.
        args = fx.tls_inputs(link_index=fx.TLS_INDEX_RVA + 8, index_entry=True)
        args['symbol_map']['symbols'][fx.TLS_INDEX]['rva'] = fx.TLS_INDEX_RVA + 8
        self.assertRejected(compare(**args), 'tls-index-mismatch')

    def test_candidate_defining_tls_index_rejected(self):
        report = compare(**fx.tls_inputs(unit=fx.tls_unit(define_index=True)))
        self.assertRejected(report, 'unsupported-relocation', '_tls_index')

    def test_image_without_tls_directory_rejected(self):
        image = self.linked(directory=None)
        self.assertRejected(compare(**fx.tls_inputs(image=image)), 'tls-directory-missing')

    def test_template_inside_another_section_passes(self):
        # MSVC can merge the template into .rdata at a non-zero offset; SECREL stays template-relative.
        self.assertPass(compare(**fx.tls_inputs(tls=fx.tls_layout(start=fx.TLS_SECTION_RVA + 0x10))))

    def test_template_relative_not_section_relative(self):
        # An image whose fields are offsets from the section start, not the template start, fails.
        tls = fx.tls_layout(start=fx.TLS_SECTION_RVA + 0x10)
        image = self.linked(offset=fx.TLS_OFFSET + 0x10, start=fx.TLS_SECTION_RVA + 0x10)
        self.assertRejected(compare(**fx.tls_inputs(tls=tls, image=image)), 'relocation-target-mismatch', 'SECREL')

    def test_template_past_section_end_rejected(self):
        tls = fx.tls_layout(size=0x1001)
        self.assertRejected(compare(**fx.tls_inputs(tls=tls)), 'unsupported-tls-layout')

    def test_short_tls_directory_rejected(self):
        tls = fx.tls_layout(directory_size=24)
        self.assertRejected(compare(**fx.tls_inputs(tls=tls)), 'malformed-tls-directory')

    def test_template_bounds_reversed_rejected(self):
        tls = fx.tls_layout(size=-0x10)
        self.assertRejected(compare(**fx.tls_inputs(tls=tls)), 'malformed-tls-directory')

    def test_other_relocation_against_thread_local_rejected(self):
        unit = fx.tls_unit(secrel_kind=fx.REL32)
        self.assertRejected(compare(**fx.tls_inputs(unit=unit, image=self.linked())), 'tls-reference-kind')

    def test_malformed_thread_local_entries_rejected(self):
        for entry in ({'kind': 'thread-local', 'tls_offset': fx.TLS_OFFSET, 'rva': 0x5768, 'size': 4},
                      {'kind': 'thread-local', 'size': 4}, {'kind': 'tls', 'tls_offset': fx.TLS_OFFSET, 'size': 4},
                      {'tls_offset': fx.TLS_OFFSET, 'size': 4}, tls_entry(size=0)):
            with self.subTest(entry=entry):
                self.assertRejected(compare(**fx.tls_inputs(var_entry=entry)), 'invalid-symbol-map')
        args = fx.tls_inputs()
        args['symbol_map']['symbols'][fx.TLS_INDEX] = tls_entry(offset=0)
        self.assertRejected(compare(**args), 'invalid-symbol-map', '_tls_index')

    def test_thread_local_task_symbol_or_fold_rejected(self):
        args = fx.tls_inputs()
        args['symbol_map']['symbols'][fx.TLS_FUNCTION] = tls_entry(offset=0)
        self.assertRejected(compare(**args), 'symbol-map-conflict', 'thread-local')
        args = fx.tls_inputs(index_entry=True)
        args['symbol_map']['folds'] = [[fx.TLS_VAR, fx.TLS_INDEX]]
        self.assertRejected(compare(**args), 'invalid-symbol-map', 'folds')

    def test_bad_thread_local_entry_fails_any_function(self):
        # Thread-local entries are checked against the image even when the function does not use them.
        args = fx.inputs()
        args['symbol_map']['symbols']['?tOther@@3HA'] = tls_entry()
        self.assertRejected(compare(**args), 'tls-directory-missing')

    def test_maps_without_thread_local_entries_need_no_tls_directory(self):
        self.assertEqual(compare(**fx.inputs())['result'], 'pass')

    def test_tls_reports_contain_no_bytes(self):
        reports = [compare(**fx.tls_inputs()), compare(**fx.tls_inputs(var_entry=tls_entry(offset=fx.TLS_OFFSET + 4)))]
        windows = {fx.TLS_CODE[i:i + 4].hex() for i in range(len(fx.TLS_CODE) - 3)} - {'00000000'}
        for report in reports:
            text = json.dumps(report).lower()
            self.assertEqual([w for w in windows if w in text], [], report['reason'])


if __name__ == '__main__':
    unittest.main()
