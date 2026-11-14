"""Mutation-family generation retains member identity and rejects shape drift."""
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import locked_array_template_v1 as template


class LockedArrayTemplateTests(unittest.TestCase):
    def test_variants_emit_only_the_selected_method_and_unique_abi_names(self):
        for kind, size, method, other in [('F063', 373, 'Add', 'Remove'), ('F068', 386, 'Remove', 'Add')]:
            owner, array, selected, ah, header, cpp = template.emit(kind, 0x1000, size)
            self.assertEqual(selected, method)
            self.assertIn(f'void {owner}::{method}(', cpp)
            self.assertNotIn(f'void {owner}::{other}(', cpp)
            self.assertIn(f'#include "{owner}.h"', cpp)
            self.assertIn(f'#include "{array}.h"', header)
            self.assertIn('namespace p117_1000', ah)
            self.assertIn('MIT License', ah)
            self.assertEqual(template.emit(kind, 0x1000, size), template.emit(kind, 0x1000, size))

    def test_rejects_another_extent_or_variant(self):
        for kind, rva, size in [('F055', 1, 575), ('F063', 1, 386), ('F068', -1, 386), ('F063', True, 373)]:
            with self.assertRaises(ValueError):
                template.emit(kind, rva, size)

    def test_origin_binds_the_complete_template(self):
        digest = hashlib.sha256(Path(template.__file__).read_bytes()).hexdigest()
        self.assertEqual(template.origin('F063')['template_digest'], digest)
        self.assertNotEqual(template.origin('F063')['family'], template.origin('F068')['family'])
