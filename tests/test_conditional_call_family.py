"""Original synthetic enrollment-filter tests; no game inputs."""
import copy
import struct
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import conditional_call_family as family


class ConditionalCallFamilyTests(unittest.TestCase):
    def setUp(self):
        self.rva = 4096
        self.raw = bytearray(b'synthetic reference fixture')
        self.offsets = (4, 12)
        self.targets = (8192, 12288)
        self.fields = []
        for off, target in zip(self.offsets, self.targets):
            struct.pack_into('<i', self.raw, off, target - self.rva - off - 4)
            self.fields.append((off, 4, 'REL32', 0, target))
        self.section = NS(data=bytes(len(self.raw)), relocs=[NS(offset=o, kind=4, symbol=i+1)
                                                           for i, o in enumerate(self.offsets)])
        data = bytearray(self.raw)
        for off in self.offsets:
            data[off:off+4] = bytes(4)
        self.section.data = bytes(data)
        self.candidate = NS(symbols={0: NS(name='Example', is_function=True, storage=2, value=0, section=1),
                                    1: NS(name=family.STATE), 2: NS(name=family.CALLBACK)},
                            section=lambda n: self.section)
        self.image = NS(image_base=0, read=lambda *args: (None, bytes(self.raw)),
                        section_for=lambda target: NS())

    def extract(self):
        with patch.object(family.imagemodel, 'field_records',
                          return_value=(self.fields, [], set(), len(self.raw))):
            return family.extract(self.image, self.rva, len(self.raw), self.candidate, 'Example')

    def test_each_reference_is_independently_bound(self):
        self.assertEqual(self.extract(), dict(zip((family.STATE, family.CALLBACK), self.targets)))

    def test_instruction_change_is_rejected(self):
        self.raw[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'instruction shape'):
            self.extract()

    def test_inconsistent_decoded_target_is_rejected(self):
        self.fields[0] = (*self.fields[0][:-1], 9999)
        with self.assertRaisesRegex(ValueError, 'target binding'):
            self.extract()

    def test_extra_reference_is_rejected(self):
        self.fields.append((20, 4, 'REL32', 0, 16384))
        with self.assertRaisesRegex(ValueError, 'reference field'):
            self.extract()

    def test_reference_kind_change_is_rejected(self):
        self.fields[0] = (4, 4, 'ADDR32NB', 0, 8192)
        with self.assertRaisesRegex(ValueError, 'reference kind'):
            self.extract()

    def test_internal_symbol_is_rejected(self):
        self.candidate.symbols[0].storage = 3
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.extract()

    def test_incomplete_section_is_rejected(self):
        self.section.data += b'!'
        with self.assertRaisesRegex(ValueError, 'extent'):
            self.extract()

    def test_emission_has_one_interface_and_unique_free_helpers(self):
        h, cpp = family.emit([4096, 8192])
        self.assertEqual(h.count('struct ConditionalVirtualCall'), 1)
        for rva in (4096, 8192):
            self.assertIn('extern "C" void ' + family.symbol(rva), h)
            self.assertIn('extern "C" void ' + family.symbol(rva), cpp)
        self.assertNotIn('padding', h + cpp)

    def test_duplicate_population_is_rejected(self):
        with self.assertRaises(ValueError):
            family.emit([4096, 4096])


if __name__ == '__main__':
    unittest.main()
