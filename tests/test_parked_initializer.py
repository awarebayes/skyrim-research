"""Original synthetic reference fixtures for the parked initializer extraction."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import parked_initializer_generate_v2 as generate
import parked_initializer_template_v2 as template


class ParkedInitializer(unittest.TestCase):
    def setUp(self):
        self.base = 0x10000000
        # These are synthetic references, not a target listing or byte fixture.
        self.rows = [[0, '', 'call 0x10001000'],
                     [1, '', 'jmp 0x10002000'],
                     [2, '', 'lea rdx, [rip] # 0x10003000'],
                     [3, '', 'lea rcx, [rip] # 0x10004000'],
                     [4, '', 'mov esi, 0x48']]
        self.actions = [0x5000, 0x6000]
        self.cleanup = [[[0, '', 'jmp 0x10007000']], [[0, '', 'jmp 0x10008000']]]

    def test_complete_reference_row(self):
        row = generate.extract(self.rows, self.base, 0x8640, self.actions, self.cleanup)
        self.assertEqual(row, {'manager-rva': 0x1000, 'atexit-rva': 0x2000,
                              'object-rva': 0x3000, 'teardown-rva': 0x4000,
                              'tls-offset': 0x48, 'storage-destroy-rva': 0x7000,
                              'context-destroy-rva': 0x8000})

    def test_incomplete_or_ambiguous_extraction_is_refused(self):
        cases = [(self.rows[:-1], self.actions, self.cleanup),
                 (self.rows + [self.rows[-1]], self.actions, self.cleanup),
                 (self.rows, self.actions[:1], self.cleanup),
                 (self.rows, self.actions, self.cleanup[:1]),
                 (self.rows, self.actions, [self.cleanup[0] * 2, self.cleanup[1]])]
        for rows, actions, cleanup in cases:
            with self.subTest(rows=rows, actions=actions, cleanup=cleanup):
                with self.assertRaises(ValueError):
                    generate.extract(rows, self.base, 0x8640, actions, cleanup)

    def test_only_declared_family_extent_is_admitted(self):
        for args in [(0x1000, 106, 0x8640), (0x1000, 116, 0x7c40), (-1, 116, 0x8640)]:
            with self.assertRaises(ValueError):
                template.emit(*args)
        cls, header, cpp, origin, params = template.emit(0x1000, 116, 0x8640)
        self.assertIn('Storage value;', header)
        self.assertIn('Sibling source:', header)
        self.assertEqual(origin['template_digest'], template.template_digest())
        self.assertEqual(params, {'entry-rva': 0x1000, 'size': 116})
        self.assertIn(f'static {cls} object;', cpp)
        recipe = json.loads((Path(__file__).resolve().parents[1] / template.RECIPE).read_text())
        self.assertEqual(recipe['flags'][-1], '/Os')


if __name__ == '__main__':
    unittest.main()
