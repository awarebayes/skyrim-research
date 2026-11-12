"""tools/analysis/x64.py and imagemodel.py on original synthetic encodings and images (no game data)."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'analysis'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import imagemodel  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402
import x64  # noqa: E402


def one(hexstr, ip=0x1000):
    return x64.decode(bytes.fromhex(hexstr), 0, ip)


class DecoderTests(unittest.TestCase):
    def test_lengths_and_fields(self):
        cases = [
            # (encoding, length, rip offset, rel (offset, size), imm (offset, size))
            ('488b0510000000', 7, 3, None, None),            # mov rax, [rip+0x10]
            ('e800010000', 5, None, (1, 4), None),           # call rel32
            ('0f8400010000', 6, None, (2, 4), None),         # je rel32
            ('7405', 2, None, (1, 1), None),                 # je rel8
            ('660f1f440000', 6, None, None, None),           # nop word [rax+rax]
            ('c4e2791805f0ffffff', 9, 5, None, None),        # vbroadcastss xmm0, [rip-0x10]
            ('48c744240801000000', 9, None, None, (5, 4)),   # mov qword [rsp+8], 1
            ('f6c201', 3, None, None, (2, 1)),               # test dl, 1
            ('830500000000' '01', 7, 2, None, (6, 1)),       # add dword [rip+0], 1
            ('48b80123456789abcdef', 10, None, None, (2, 8)),  # mov rax, imm64
            ('f00fb14f04', 5, None, None, None),             # lock cmpxchg [rdi+4], ecx
            ('8b8c8a00000000', 7, None, None, None),         # mov ecx, [rdx+rcx*4+disp32]
            ('c3', 1, None, None, None),
        ]
        for enc, length, rip, rel, imm in cases:
            with self.subTest(enc=enc):
                ins = one(enc)
                self.assertEqual(ins.length, length)
                self.assertEqual(ins.rip, rip)
                self.assertEqual(ins.rel, rel)
                self.assertEqual(ins.imm, imm)

    def test_targets(self):
        self.assertEqual(one('e800010000', 0x1000).target, 0x1105)
        self.assertEqual(one('488b05f0ffffff', 0x2000).rip_target, 0x2007 - 0x10)
        sib = one('8b8c8a10203000')
        self.assertEqual((sib.base, sib.index, sib.disp[2]), (2, 1, 0x302010))

    def test_flow_and_register_abstraction(self):
        self.assertEqual(one('ffd0').flow, x64.ICALL)
        self.assertEqual(one('ffe1').flow, x64.IJMP)
        self.assertEqual(one('cc').flow, x64.INT3)
        # mov rax,[rcx+8] and mov rdx,[rbx+8]: same key once registers are abstracted.
        self.assertEqual(one('488b4108').key, one('488b5308').key)
        self.assertNotEqual(one('488b4108').key, one('488b4110').key)
        # Stack displacements are frame-specific and left out of the key.
        self.assertEqual(one('488b442420').key, one('488b442440').key)

    def test_invalid_and_truncated(self):
        with self.assertRaises(x64.DecodeError):
            one('06')
        with self.assertRaises(x64.DecodeError):
            x64.decode(bytes.fromhex('e80001'), 0, 0)


class FieldTests(unittest.TestCase):
    """The decoded reference fields equal the synthetic object's relocations: the comparator's set."""

    def test_fields_equal_relocations(self):
        rva = fx.LAYOUT[fx.FUNCTION]
        image = fx.pe_image()
        code = image[0x400 + rva - 0x1000:0x400 + rva - 0x1000 + len(fx.CODE)]
        fields, _, flags, end = imagemodel.field_records(code, rva, len(code), 0x140000000, rva + len(code))
        kinds = {fx.REL32: ('REL32', 0), fx.REL32_1: ('REL32', 1)}
        self.assertEqual([(f[0], f[2], f[3]) for f in fields],
                         [(off, *kinds[kind]) for off, _sym, kind in fx.RELOCS])
        self.assertEqual([f[4] for f in fields], [fx.LAYOUT[sym] for _off, sym, _k in fx.RELOCS])
        self.assertEqual(end, len(code))
        self.assertEqual(flags, set())

    def write_image(self, tmp, blob, rva, size):
        img, exp = Path(tmp) / 'image', Path(tmp) / 'export.txt'
        img.write_bytes(blob)
        exp.write_text('F 0x%x %d 1 Synthetic\n' % (rva, size))
        return imagemodel.Image(str(img), str(exp))

    def test_switch_table_fields(self):
        unit = fx.switch_unit()
        placement = unit.default_placement()
        image = unit.link({}, placement)
        rva = placement[1]
        with tempfile.TemporaryDirectory() as tmp:
            im = self.write_image(tmp, image, rva, 0x31)
            r = im.analyse(0)
        self.assertNotIn('error', r)
        self.assertEqual(r['size'], 0x40)
        self.assertEqual(r['table_entries'], 3)
        relocs = sorted(off for off, _sym, _kind in unit.sections[0][2])
        self.assertEqual(sorted(off for off, _k, _t in r['targets']) + [], [0x08])
        self.assertEqual(r['nfields'], len(relocs))

    def test_masked_digest_ignores_targets_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            rva = fx.LAYOUT[fx.FUNCTION]
            a = self.write_image(tmp + '/', fx.pe_image(), rva, len(fx.CODE)).analyse(0)
        with tempfile.TemporaryDirectory() as tmp:
            b = self.write_image(tmp, fx.pe_image(link_addresses={fx.BASE: 0x2014}), rva, len(fx.CODE)).analyse(0)
        with tempfile.TemporaryDirectory() as tmp:
            c = self.write_image(tmp, fx.pe_image(patch={0x1A: 0x30}), rva, len(fx.CODE)).analyse(0)
        self.assertEqual(a['masked'], b['masked'])
        self.assertNotEqual(a['exact'], b['exact'])
        self.assertNotEqual(a['masked'], c['masked'])
        self.assertEqual([t for t in a['targets'] if t[0] != 0x0D], [t for t in b['targets'] if t[0] != 0x0D])


if __name__ == '__main__':
    unittest.main()
