import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import empty_teardown_family_v1 as specialized
import primitive_leaf_template_v1 as shared
import family_review


class TeardownFamilyTests(unittest.TestCase):
    def test_comparison_forms_have_distinct_origins_without_source_changes(self):
        old = shared.emit(0x1234, 3, 'empty', 'teardown')
        new = specialized.emit(0x1234, 3)
        for key in ('header', 'source', 'symbol', 'parameters'):
            self.assertEqual(new[key], old[key])
        self.assertNotEqual(new['origin']['family'], shared.origin('empty')['family'])
        self.assertEqual(new['origin']['template_digest'], old['origin']['template_digest'])
        family_review.origin_valid(new['origin'])

    def test_specialized_extraction_keeps_the_complete_shape_gate(self):
        self.assertEqual(specialized.extract_parameters(0x1234, bytes((194, 0, 0))),
                         {'entry-rva': 0x1234, 'size': 3, 'kind': 'teardown'})
        with self.assertRaises(ValueError):
            specialized.extract_parameters(0x1234, bytes((194, 8, 0)))


if __name__ == '__main__':
    unittest.main()
