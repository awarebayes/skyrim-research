"""Read-only PE/RTTI binding audit, independent of the disassembler and catalog writer.

Only typed metadata is emitted. No image bytes, instruction listings, or input paths
are serialized. This is analysis evidence, never a comparator or acceptance result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


class Image:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        pe = struct.unpack_from('<I', self.data, 0x3c)[0]
        if self.data[pe:pe + 4] != b'PE\0\0':
            raise ValueError('not a PE image')
        count = struct.unpack_from('<H', self.data, pe + 6)[0]
        size = struct.unpack_from('<H', self.data, pe + 20)[0]
        opt = pe + 24
        if struct.unpack_from('<H', self.data, opt)[0] != 0x20b:
            raise ValueError('PE32+ required')
        self.base = struct.unpack_from('<Q', self.data, opt + 24)[0]
        self.sections = []
        for i in range(count):
            pos = opt + size + 40 * i
            virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', self.data, pos + 8)
            self.sections.append((rva, raw_size, raw))

    def read(self, rva, size):
        for start, count, raw in self.sections:
            if start <= rva and rva + size <= start + count:
                return self.data[raw + rva - start:raw + rva - start + size]
        raise ValueError('metadata reference outside initialized image')

    def number(self, rva, fmt='I'):
        return struct.unpack('<' + fmt, self.read(rva, struct.calcsize('<' + fmt)))[0]

    def name(self, descriptor):
        result = bytearray()
        for i in range(4096):
            value = self.read(descriptor + 16 + i, 1)[0]
            if value == 0:
                return result.decode('ascii')
            result.append(value)
        raise ValueError('unterminated RTTI name')

    def table(self, rva):
        col = self.number(rva - 8, 'Q') - self.base
        if self.number(col) != 1 or self.number(col + 20) != col:
            raise ValueError('unsupported complete-object locator')
        hierarchy = self.number(col + 16)
        count = self.number(hierarchy + 8)
        if not 1 <= count <= 1024:
            raise ValueError('invalid base-class count')
        array = self.number(hierarchy + 12)
        bases = []
        for i in range(count):
            descriptor = self.number(array + 4 * i)
            bases.append(dict(type_raw=self.name(self.number(descriptor)),
                              mdisp=self.number(descriptor + 8, 'i'),
                              pdisp=self.number(descriptor + 12, 'i'),
                              vdisp=self.number(descriptor + 16, 'i')))
        return dict(type_raw=self.name(self.number(col + 12)),
                    offset=self.number(col + 4), bases=bases)


def audit(image, catalog):
    if image.sha256 != catalog['image_sha256']:
        raise ValueError('target image hash mismatch')
    rows = []
    for member in catalog['members']:
        rva = member['rva']
        # Operand positions belong to the pinned 43-byte deleting-leaf contract.
        # The generator's separate disassembler validates the instruction shape;
        # here the signed operands are read directly from the measured image.
        stored = rva + 13 + image.number(rva + 9, 'i')
        allocation = image.number(rva + 25)
        deallocator = rva + 34 + image.number(rva + 30, 'i')
        branch = rva + 24 + image.number(rva + 23, 'b')
        owner = image.table(member['owner_table'])
        actual = image.number(member['owner_table'] + 8 * member['owner_slot'], 'Q') - image.base
        table = image.table(stored)
        if (actual != rva or owner['type_raw'] != member['owner_rtti']
                or owner['offset'] != 0 or table['offset'] != 0
                or stored != member['stored_table'] or allocation != member['object_size']
                or branch != rva + 34):
            raise ValueError(f'0x{rva:x}: target binding disagreement')
        if not any(b['type_raw'] == table['type_raw'] and b['mdisp'] == 0
                   and b['pdisp'] == -1 for b in owner['bases']):
            raise ValueError(f'0x{rva:x}: written base not at primary subobject')
        rows.append(dict(rva=rva, owner_table=member['owner_table'],
                         owner_slot=member['owner_slot'], observed_slot_rva=actual,
                         owner_type_raw=owner['type_raw'], owner_bases=owner['bases'],
                         stored_table=stored, stored_type_raw=table['type_raw'],
                         object_size=allocation, deallocator_rva=deallocator))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    raw = args.catalog.read_bytes()
    catalog = json.loads(raw)
    image = Image(args.image)
    rows = audit(image, catalog)
    result = dict(audit_schema=1, build_id=catalog['build_id'], image_sha256=image.sha256,
                  catalog_sha256=hashlib.sha256(raw).hexdigest(),
                  audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  row_count=len(rows), facts=rows)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(f'independent target binding audit: {len(rows)} rows agree')


if __name__ == '__main__':
    main()
