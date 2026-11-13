"""Regression reference-map preparation on original synthetic metadata."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/ghidra'))
import export_pack as ep


class RegressionSymbols(unittest.TestCase):
    def test_unit_maps_keep_references_and_declared_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'record.json').write_text(json.dumps({'symbol_map': {'path': 'unit.json'}}))
            symbols = {'AliasA': {'rva': 4096, 'size': 8}, 'AliasB': {'rva': 4096, 'size': 8},
                       'LocalReference': {'rva': 8192, 'size': None}}
            folds = [['AliasA', 'AliasB']]
            (root / 'unit.json').write_text(json.dumps({'symbols': symbols, 'folds': folds}))
            result, actual_folds, origins = ep.regression_symbols(
                [{'record': 'record.json'}, {'record': 'record.json'}], 'synthetic', root)
            self.assertEqual(result, symbols)
            self.assertEqual(actual_folds, folds)
            self.assertEqual(len(origins), len(symbols))
            self.assertTrue(all(x['from'] == 'unit.json' for x in origins))

    def test_conflicting_regression_names_refuse_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i, address in enumerate((4096, 8192)):
                (root / f'record{i}.json').write_text(json.dumps({'symbol_map': {'path': f'map{i}.json'}}))
                (root / f'map{i}.json').write_text(json.dumps({'symbols': {'Reference': {'rva': address}}}))
            with self.assertRaisesRegex(ValueError, 'conflicting bindings'):
                ep.regression_symbols([{'record': f'record{i}.json'} for i in range(2)], 'synthetic', root)

    def test_empty_regressions_need_no_map(self):
        self.assertEqual(ep.regression_symbols([], 'synthetic'), ({}, [], []))


if __name__ == '__main__':
    unittest.main()
