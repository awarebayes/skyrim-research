"""The eight-byte family must never admit size-forcing storage."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import deleting_eight_template_v3 as template
import deleting_eight_generate_v3 as generator
from test_deleting_leaf import synthetic_rows


class EightBytePolicyTests(unittest.TestCase):
    def test_larger_and_noninteger_sizes_are_refused(self):
        for size in (0,7,9,16,24,491576,True):
            with self.assertRaises(ValueError):template.emit(0x1000,size)
        emitted=template.emit(0x1000,8)
        code='\n'.join(line for line in emitted['header'].splitlines() if not line.startswith('//'))
        self.assertNotIn('[',code)
        self.assertNotIn('unsigned char',code)
        self.assertIn('class DeletingLeaf1000',code)

    def test_extraction_cannot_enroll_storage_bearing_shape(self):
        rows=synthetic_rows()
        with self.assertRaises(ValueError):generator.extract(rows,0x1000,0x140000000)
        rows[7][2]='mov edx, 0x8'
        self.assertEqual(generator.extract(rows,0x1000,0x140000000)['object-size'],8)


if __name__=='__main__':unittest.main()
