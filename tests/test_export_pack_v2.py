"""export_pack's contract v2 suitability on original synthetic images (no Ghidra, no game data).

Each image is linked from the comparator's own synthetic units (tests/synthetic_pecoff.py), so
the size and map entries the exporter derives from the image alone can be checked by running the
comparator with them: if the exporter sized the function or named its handler and caught types
wrongly, the comparator fails.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'ghidra'))
import export_pack as ep  # noqa: E402
from compare import compare  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402

ADDRLIB = {'by_rva': {}}


def gmeta(rva, size, computed_jumps=0, computed_targets=0):
    return {'found': True, 'ghidra_name': 'FUN', 'ranges': [(rva, rva + size)], 'n_instr': 1,
            'computed_jumps': computed_jumps, 'computed_targets': computed_targets, 'thunk': False,
            'fp_arith': 0, 'cond_branches': 0, 'indirect_calls': 0}


class ExportV2Tests(unittest.TestCase):
    def facts(self, unit, symbol, analysed_size=None, **g):
        image = unit.link(fx.image_externals())
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / 'image.bin'
        path.write_bytes(image)
        img = ep.ImageFacts(path)
        # The synthetic thunks import nothing; name them as the private config would.
        img.handler_names = {rva: name for name, rva in fx.HANDLER_THUNKS.items()}
        rva = fx.section_rva(unit, symbol)
        size = len(unit.sections[next(s for s in unit.symbols if s[0] == symbol)[2] - 1][1])
        fact = ep.classify(img, ADDRLIB, [], rva, gmeta(rva, analysed_size or size, **g), [])
        return fact, image, rva, size

    def comparator_with_exporter_map(self, unit, symbol, fact, image):
        """Run the comparator with the size and EH map entries the exporter derived."""
        externals = {k: v for k, v in fx.image_externals().items() if k not in fx.HANDLER_THUNKS}
        eh_map = {r['symbol']: {'rva': r['target_rva'], 'size': None} for r in fact['references']
                  if r['resolution'] in ('eh-handler', 'eh-type')}
        args = fx.unit_inputs(unit, symbol, externals, image=image, extra_map=eh_map)
        args['task']['size'] = fact['size']
        return compare(**args)

    def test_chained_function_sized_to_last_chained_entry(self):
        fact, image, rva, size = self.facts(fx.chain_unit(), fx.CHAIN_FUNCTION, analysed_size=8)
        self.assertEqual((fact['size'], fact['chained_entries']), (size, 2))
        self.assertNotIn('multiple-pdata', fact['reasons'])
        self.assertNotIn('chained-unwind', fact['reasons'])
        self.assertEqual(fact['verdict'], 'supported')
        self.assertEqual(self.comparator_with_exporter_map(fx.chain_unit(), fx.CHAIN_FUNCTION, fact, image)['result'],
                         'pass')

    def test_switch_function_sized_over_its_table(self):
        code_end = fx.SWITCH_TABLE - 3
        fact, image, rva, size = self.facts(fx.switch_unit(), fx.SWITCH_FUNCTION, analysed_size=code_end,
                                            computed_jumps=1, computed_targets=3)
        self.assertEqual((fact['size'], fact['switch_table_entries']), (size, 3))
        self.assertNotIn('jump-table', fact['reasons'])
        self.assertEqual(self.comparator_with_exporter_map(fx.switch_unit(), fx.SWITCH_FUNCTION, fact, image)['result'],
                         'pass')

    def test_switch_without_table_after_code_stays_unsupported(self):
        unit = fx.chain_unit()
        fact, *_ = self.facts(unit, fx.CHAIN_FUNCTION, computed_jumps=1, computed_targets=3)
        self.assertIn('jump-table', fact['reasons'])

    def test_cxx_catch_emits_handler_caught_type_and_funclets(self):
        unit = fx.catch_unit()
        fact, image, rva, size = self.facts(unit, fx.CATCH_FUNCTION)
        self.assertEqual(fact['reasons'], [])
        symbols = {r['symbol']: r['target_rva'] for r in fact['references']}
        self.assertEqual(symbols['__CxxFrameHandler3'], fx.HANDLER_THUNKS['__CxxFrameHandler3'])
        self.assertEqual(symbols[fx.CATCH_TYPE], fx.catch_map(unit)[fx.CATCH_TYPE]['rva'])
        funclets = {f['rva']: f['size'] for f in fact['eh']['funclets']}
        catch0 = fx.section_rva(unit, '?catch$0@?0??SyntheticCatch@@4HA')
        self.assertEqual(funclets[hex(catch0)], 0x21)
        self.assertIsNone(funclets[hex(catch0 + 0x21)])     # leaf unwind funclet: no .pdata
        self.assertEqual(self.comparator_with_exporter_map(unit, fx.CATCH_FUNCTION, fact, image)['result'], 'pass')

    def test_seh_scope_table_with_filter_funclet(self):
        unit = fx.seh_unit()
        fact, image, *_ = self.facts(unit, fx.SEH_FUNCTION)
        self.assertEqual(fact['reasons'], [])
        self.assertEqual(fact['eh']['handlers'], {'__C_specific_handler': hex(fx.HANDLER_THUNKS['__C_specific_handler'])})
        self.assertEqual(len(fact['eh']['funclets']), 1)
        self.assertEqual(self.comparator_with_exporter_map(unit, fx.SEH_FUNCTION, fact, image)['result'], 'pass')

    def test_handler_outside_contract_is_unsupported(self):
        fact, *_ = self.facts(fx.catch_unit(handler='__CxxFrameHandler4'), fx.CATCH_FUNCTION)
        self.assertIn('unsupported-eh-handler', fact['reasons'])

    def test_unnamed_handler_is_unsupported_with_its_reason(self):
        unit = fx.catch_unit()
        image = unit.link(fx.image_externals())
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'i').write_bytes(image)
            img = ep.ImageFacts(Path(tmp) / 'i')
            rva = fx.section_rva(unit, fx.CATCH_FUNCTION)
            fact = ep.classify(img, ADDRLIB, [], rva, gmeta(rva, len(fx.CATCH_CODE)), [])
        self.assertIn('eh-handler-unidentified', fact['reasons'])

    def test_unknown_funcinfo_magic_is_unsupported(self):
        fact, *_ = self.facts(fx.catch_unit(magic=0x19930521), fx.CATCH_FUNCTION)
        self.assertIn('eh-funcinfo-unsupported', fact['reasons'])


if __name__ == '__main__':
    unittest.main()
