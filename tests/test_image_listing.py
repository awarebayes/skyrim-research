import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'verifier'))
import image_listing  # noqa: E402

# Synthetic map rows in the MSVC layout (section:offset, name, Rva+Base, flags, object).
MAP = """ Preferred load address is 0000000180000000

  Address         Publics by Value              Rva+Base               Lib:Object

 0001:00000000       ?first@@YAXXZ              0000000180001000 f   a.obj
 0001:00000020       ?second@@YAXXZ             0000000180001020 f   a.obj
 0002:00000010       p9_d0                      0000000180003010     stubs.obj
"""


class MapTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / 'x.map'
        self.path.write_text(MAP)

    def tearDown(self):
        self.dir.cleanup()

    def test_reads_public_rows_sorted(self):
        rows = image_listing.read_map(self.path)
        self.assertEqual([n for _, n in rows], ['?first@@YAXXZ', '?second@@YAXXZ', 'p9_d0'])
        self.assertEqual(rows[0][0], 0x180001000)

    def test_locate_gives_containing_symbol_and_offset(self):
        rows = image_listing.read_map(self.path)
        addrs = [a for a, _ in rows]
        self.assertEqual(image_listing.locate(rows, addrs, 0x180001024), ('?second@@YAXXZ', 4))
        self.assertEqual(image_listing.locate(rows, addrs, 0x180003018), ('p9_d0', 8))
        self.assertEqual(image_listing.locate(rows, addrs, 0x180000500), (None, 0))

    def test_missing_symbol_is_an_error(self):
        with self.assertRaises(ValueError):
            image_listing.listing('none.dll', self.path, '?absent@@YAXXZ', 'llvm-objdump')


if __name__ == '__main__':
    unittest.main()
