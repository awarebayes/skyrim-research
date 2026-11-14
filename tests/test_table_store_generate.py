"""Synthetic complete-extent, RTTI binding and natural-layout checks."""
from pathlib import Path
from types import SimpleNamespace
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import table_store_generate as generator
import table_store_template_v1 as template


def rows(target=0x2000):
    texts = [f'lea rax, [rip + 0x100] # 0x{0x140000000+target:x}',
             'mov qword ptr [rcx], rax', 'ret']
    return [[offset, ' '.join(['xx']*size), text, []]
            for offset, size, text in zip((0, 7, 10), (7, 3, 1), texts)]


def facts(offset=0, construction=0):
    values = {0x1ff8: struct.pack('<Q', 0x140003000),
              0x3000: struct.pack('<6I', 1, offset, construction, 0x4000, 0x5000, 0x3000),
              0x2000: struct.pack('<Q', 0x140006000)}
    img = SimpleNamespace(size_of_image=0x10000, read=lambda r, n: values[r],
                          section=lambda r: SimpleNamespace(flags=generator.ep.EXEC))
    rtti = SimpleNamespace(base=0x140000000, reloc={0x1ff8},
        vftables={0x2000: (offset, 0x4000, 0x5000)},
        td_name=lambda td: '.?AVSynthetic@@',
        chain=lambda chd: (['.?AVSynthetic@@'], ['.?AVSynthetic@@']))
    return img, rtti


class TableStoreTests(unittest.TestCase):
    def test_reference_is_independent(self):
        for rva, target in ((0x1000, 0x2000), (0x1200, 0x2500)):
            self.assertEqual(generator.extract(rows(target), rva, 0x140000000),
                             {'entry-rva': rva, 'size': 11, 'table-rva': target})

    def test_whole_shape_required(self):
        for index, text in ((1, 'mov qword ptr [rcx + 0x8], rax'), (2, 'ret 0x8')):
            changed = rows()
            changed[index][2] = text
            with self.assertRaises(ValueError):
                generator.extract(changed, 0x1000, 0x140000000)
        for changed in (rows()[:-1], rows()+[[11, 'xx', 'nop', []]]):
            with self.assertRaises(ValueError):
                generator.extract(changed, 0x1000, 0x140000000)

    def test_rtti_relation_is_bound(self):
        img, rtti = facts()
        params = generator.bind_rtti(img, rtti, generator.extract(rows(), 0x1000, rtti.base))
        self.assertEqual(params['type-descriptor-rva'], 0x4000)
        self.assertEqual(params['locator-rva'], 0x3000)
        rtti.vftables[0x2000] = (0, 0x4008, 0x5000)
        with self.assertRaisesRegex(ValueError, 'disagreement'):
            generator.bind_rtti(img, rtti, {'table-rva': 0x2000})

    def test_nonprimary_or_missing_locator_rejected(self):
        for offset, construction in ((8, 0), (0, 4)):
            with self.assertRaises(ValueError):
                generator.bind_rtti(*facts(offset, construction), {'table-rva': 0x2000})
        img, rtti = facts()
        rtti.reloc.clear()
        with self.assertRaises(ValueError):
            generator.bind_rtti(img, rtti, {'table-rva': 0x2000})

    def test_no_size_forcing_storage(self):
        e = template.emit(0x1000)
        self.assertIn('virtual ~TableStoreLeaf1000();', e['header'])
        self.assertIn('TableStoreLeaf1000::~TableStoreLeaf1000() {}', e['source'])
        self.assertNotIn('static_assert', e['header'])
        body = e['header'].split('class TableStoreLeaf1000 {', 1)[1]
        self.assertNotIn('[', body)
        self.assertEqual(body.count(';'), 2)
        for rva in (-1, True, '0x1000'):
            with self.assertRaises(ValueError):
                template.emit(rva)


if __name__ == '__main__':
    unittest.main()
