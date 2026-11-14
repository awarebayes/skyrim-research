"""Synthetic instruction rows; no game bytes or private paths."""
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import deleting_wrapper_generate as generator
import deleting_wrapper_template_v1 as template


class WrapperTests(unittest.TestCase):
    def rows(self):
        offsets = [0, 5, 6, 10, 12, 15, 20, 23, 25, 30, 33, 38, 43, 46, 50, 51, 52]
        text = ['mov qword ptr [rsp + 0x8], rbx', 'push rdi', 'sub rsp, 0x20',
                'mov ebx, edx', 'mov rdi, rcx', 'call 0x3000', 'test bl, 0x1',
                'je 0x2026', 'mov edx, 0x8', 'mov rcx, rdi', 'call 0x4000',
                'mov rbx, qword ptr [rsp + 0x30]', 'mov rax, rdi', 'add rsp, 0x20', 'pop rdi', 'ret']
        return [[off, ' '.join(['00'] * (end-off)), ins, []]
                for off, end, ins in zip(offsets, offsets[1:], text)]

    def test_independent_calls_and_size(self):
        self.assertEqual(generator.extract(self.rows(), 0x1000, 0x1000),
                         {'entry-rva':0x1000, 'size':52, 'object-size':8,
                          'destructor-rva':0x2000, 'deallocator-rva':0x3000})

    def test_full_shape_and_branch_required(self):
        for index, text in ((7, 'je 0x2027'), (6, 'test bl, 0x2'), (5, 'jmp 0x3000')):
            rows=self.rows(); rows[index][2]=text
            with self.assertRaises(ValueError): generator.extract(rows, 0x1000, 0x1000)
        with self.assertRaises(ValueError): generator.extract(self.rows()[:-1], 0x1000, 0x1000)

    def test_no_size_forcing_storage(self):
        header=template.emit(0x1000)['header']
        self.assertIn('virtual ~DeletingWrapper1000();', header)
        self.assertNotIn('[', header)
        for size in (0, 16, 24, 4096):
            with self.assertRaises(ValueError): template.emit(0x1000, size)
