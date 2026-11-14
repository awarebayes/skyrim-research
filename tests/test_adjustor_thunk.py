"""Synthetic transfer/RTTI negatives, with no game data or instruction bytes."""
import struct
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import adjustor_thunk_generate as gen
import adjustor_thunk_template_v2 as template


class AdjustorExtractionTests(unittest.TestCase):
    def test_arithmetic_and_tailcall_are_derived(self):
        # Text markers only supply lengths; these are deliberately not machine bytes.
        rows = [[0, 'marker '*3, 'sub rcx, 0x17'], [3, 'marker '*2, 'add rcx, 0x2'],
                [5, 'marker '*5, 'jmp 0x10000400']]
        self.assertEqual(gen.extract(rows, 0x100, 10, 0x10000000),
                         {'adjustment': -21, 'callee_rva': 0x400})

    def test_hidden_effects_gaps_and_truncated_ranges_refuse(self):
        valid = [[0, 'marker '*3, 'sub rcx, 0x17'], [3, 'marker '*5, 'jmp 0x10000400']]
        cases = [valid[:1], [[1, *valid[0][1:]], valid[1]],
                 [[0, valid[0][1], 'sub rax, 0x17'], valid[1]],
                 [valid[0], [3, valid[1][1], 'call 0x10000400']],
                 [valid[0], valid[1], [8, 'marker', 'ret']]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                gen.extract(rows, 0x100, 8, 0x10000000)

    def test_wrong_owner_slot_offset_or_direct_base_refuse(self):
        image = SimpleNamespace(pe=SimpleNamespace(image_base=0x10000000))
        memory = {}
        names = {0x5000: 'SyntheticOwner', 0x5100: 'SyntheticBase'}
        def put(address, fmt, *values):
            memory[address] = struct.pack(fmt, *values)
        # Each read uses the exact synthetic format extent under test.
        put(0x1000-8, '<Q', 0x10002000)
        put(0x1100-8, '<Q', 0x10002100)
        put(0x2000, '<IIIIII', 1, 0, 0, 0x5000-16, 0x3000, 0x2000)
        put(0x2100, '<IIIIII', 1, 8, 0, 0x5000-16, 0x3000, 0x2100)
        put(0x3008, '<II', 2, 0x4000)
        put(0x4000, '<I', 0x4100)
        put(0x4004, '<I', 0x4200)
        put(0x4100, '<IIiiiI', 0x5000-16, 1, 0, -1, 0, 0)
        put(0x4200, '<IIiiiI', 0x5100-16, 0, 8, -1, 0, 0)
        put(0x1000, '<Q', 0x10000600)
        put(0x1100, '<Q', 0x10000700)
        image.read = lambda address, size: memory[address][:size]
        image._cstr = lambda address: names[address]
        member = dict(rva=0x700, size=8, primary_table=0x1000, secondary_table=0x1100,
                      slot=0, primary_slot=0, rtti_type='SyntheticOwner',layout_size=16,
                      direct_bases=[dict(type='SyntheticBase',offset=8)])
        decoded = dict(adjustment=-8, callee_rva=0x600)
        self.assertEqual(gen.reconcile(image,member,decoded)['callee-rva'], 0x600)
        for change in ({'rtti_type':'WrongOwner'}, {'rva':0x701},
                       {'direct_bases':[dict(type='SyntheticBase',offset=16)]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                gen.reconcile(image,dict(member,**change),decoded)
        with self.assertRaises(ValueError):
            gen.reconcile(image,member,dict(decoded,adjustment=-16))

    def test_owner_has_distinct_represented_product_bases(self):
        with self.assertRaises(ValueError):
            template.registration_owner('SyntheticCaster',['Item','Item'],24)
        with self.assertRaises(ValueError):
            template.emit(0x100,8,8,'../Outside',16)


if __name__ == '__main__':
    unittest.main()
