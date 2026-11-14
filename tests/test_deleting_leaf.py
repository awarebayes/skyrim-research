"""Synthetic full-shape extraction and source-form bounds."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import deleting_leaf_generate as generator
import deleting_leaf_template_v1 as template


def synthetic_rows():
    instructions = ['push rbx', 'sub rsp, 0x20',
                    'lea rax, [rip + 0x100] # 0x140002000',
                    'mov rbx, rcx', 'mov qword ptr [rcx], rax', 'test dl, 0x1',
                    'je 0x140001022', 'mov edx, 0x18', 'call 0x140003000',
                    'mov rax, rbx', 'add rsp, 0x20', 'pop rbx', 'ret']
    offsets = [0, 2, 6, 13, 16, 19, 22, 24, 29, 34, 37, 41, 42, 43]
    # Synthetic width markers, never executable bytes.
    return [[offsets[i], ' '.join(['xx']*(offsets[i+1]-offsets[i])), text, []]
            for i,text in enumerate(instructions)]


class DeletingLeafTests(unittest.TestCase):
    def test_independent_parameter_fields(self):
        rows=synthetic_rows()
        expected={'entry-rva':0x1000,'size':43,'object-size':24,
                  'table-rva':0x2000,'deallocator-rva':0x3000}
        self.assertEqual(generator.extract(rows,0x1000,0x140000000),expected)
        rows[2][2]='lea rax, [rip + 0x100] # 0x140004000'
        rows[8][2]='call 0x140005000'
        actual=generator.extract(rows,0x1000,0x140000000)
        self.assertEqual((actual['table-rva'],actual['deallocator-rva']),(0x4000,0x5000))

    def test_rejects_control_flow_and_extent_changes(self):
        for index,text in ((5,'test dl, 0x2'),(6,'je 0x140001023'),(8,'jmp 0x140003000'),(12,'ret 0x8')):
            rows=synthetic_rows();rows[index][2]=text
            with self.assertRaises(ValueError):generator.extract(rows,0x1000,0x140000000)
        with self.assertRaises(ValueError):generator.extract(synthetic_rows()[:-1],0x1000,0x140000000)

    def test_natural_destructor_and_size_bounds(self):
        for size in (8,24,1048576):
            emitted=template.emit(0x1000,size)
            self.assertIn('virtual ~DeletingLeaf1000() {}',emitted['header'])
            self.assertIn(f'== {size}',emitted['header'])
            self.assertEqual(emitted['symbol'],'??_GDeletingLeaf1000@@UEAAPEAXI@Z')
        for size in (0,7,9,1048584,True):
            with self.assertRaises(ValueError):template.emit(0x1000,size)


if __name__=='__main__':unittest.main()
