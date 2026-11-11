"""Build original synthetic x86-64 COFF objects and PE32+ images for comparator tests.

Every byte here is hand-chosen for these tests; no compiler, linker or game input is involved.
The images are shaped only enough for the comparator to read; they are not meant to run.
Fixtures are produced in memory at test time so no binary file is ever committed.
"""
import hashlib
import json
import struct

REL32, REL32_1, ADDR32NB, SECREL = 0x04, 0x05, 0x03, 0x0B

FUNCTION = 'SyntheticSum'
CALLEE = 'SyntheticAddOne'
OTHER_CALLEE = 'SyntheticZero'
BASE = 'gSyntheticBase'
COUNTER = 'gSyntheticCount'

# SyntheticSum(int *p): return SyntheticAddOne(*p) + gSyntheticBase, bumping gSyntheticCount.
CODE = bytes.fromhex(
    '4883ec28'      # +0x00 sub  rsp, 0x28
    '8b09'          # +0x04 mov  ecx, [rcx]
    'e800000000'    # +0x06 call SyntheticAddOne      (REL32 field at +0x07)
    '030500000000'  # +0x0b add  eax, [rip+gSyntheticBase]   (REL32 at +0x0d)
    '83050000000001'  # +0x11 add dword [rip+gSyntheticCount], 1 (REL32_1 at +0x13)
    '4883c428'      # +0x18 add  rsp, 0x28
    'c3')           # +0x1c ret
RELOCS = ((0x07, CALLEE, REL32), (0x0D, BASE, REL32), (0x13, COUNTER, REL32_1))
# UNWIND_INFO v1: prolog 4 bytes, one code: UWOP_ALLOC_SMALL of 0x28 at offset 4, padded to even.
XDATA = bytes.fromhex('01040100' '04420000')
CALLEE_CODE = bytes.fromhex('8d4101c3')   # lea eax, [rcx+1]; ret
OTHER_CODE = bytes.fromhex('31c0c3')      # xor eax, eax; ret

LAYOUT = {CALLEE: 0x1000, OTHER_CALLEE: 0x1008, FUNCTION: 0x1010, 'xdata': 0x2000, BASE: 0x2010, COUNTER: 0x3000}
SCN_CODE, SCN_DATA = 0x60500020, 0x40300040


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def coff_object(code=CODE, relocs=RELOCS, unwind=True):
    """Return a relocatable object defining FUNCTION in its own code section, like /Gy output."""
    strings = bytearray(4)

    def name8(name):
        raw = name.encode()
        if len(raw) <= 8:
            return raw.ljust(8, b'\0')
        offset = len(strings)
        strings.extend(raw + b'\0')
        return struct.pack('<II', 0, offset)

    symbols = [(FUNCTION, 0, 1, 0x20, 2), (CALLEE, 0, 0, 0x20, 2), (BASE, 0, 0, 0, 2), (COUNTER, 0, 0, 0, 2)]
    index = {name: i for i, (name, *_rest) in enumerate(symbols)}
    sections = [('.text$mn', bytes(code), [(off, index[sym], kind) for off, sym, kind in relocs], SCN_CODE)]
    if unwind:
        symbols += [('$unwind$' + FUNCTION, 0, 2, 0, 3), ('$pdata$' + FUNCTION, 0, 3, 0, 3)]
        pdata = struct.pack('<III', 0, len(code), 0)
        sections += [('.xdata', XDATA, [], SCN_DATA),
                     ('.pdata', pdata, [(0, 0, ADDR32NB), (4, 0, ADDR32NB), (8, 4, ADDR32NB)], SCN_DATA)]
    header_end = 20 + 40 * len(sections)
    body, headers, cursor = bytearray(), bytearray(), header_end
    for name, data, rels, flags in sections:
        raw_ptr = cursor
        rel_ptr = raw_ptr + len(data) if rels else 0
        headers += struct.pack('<8sIIIIIIHHI', name.encode(), 0, 0, len(data), raw_ptr, rel_ptr, 0, len(rels), 0, flags)
        body += data
        for off, sym, kind in rels:
            body += struct.pack('<IIH', off, sym, kind)
        cursor = header_end + len(body)
    table = b''.join(struct.pack('<8sIhHBB', name8(n), v, s, t, c, 0) for n, v, s, t, c in symbols)
    struct.pack_into('<I', strings, 0, len(strings))
    header = struct.pack('<HHIIIHH', 0x8664, len(sections), 0, cursor, len(symbols), 0, 0)
    return header + bytes(headers) + bytes(body) + table + bytes(strings)


def link(code, relocs, addresses, at):
    """Apply relocations the way a linker would, from first principles rather than comparator code."""
    out = bytearray(code)
    for off, sym, kind in relocs:
        tail = {REL32: 0, REL32_1: 1}[kind]
        struct.pack_into('<i', out, off, addresses[sym] - (at + off + 4 + tail))
    return bytes(out)


def pe_image(code=CODE, link_addresses=None, pdata=True, xdata=XDATA, text_raw_size=None, patch=None):
    """Return a PE32+ image placing FUNCTION at LAYOUT[FUNCTION] and its references per `link_addresses`."""
    addresses = dict(LAYOUT, **(link_addresses or {}))
    func_rva = LAYOUT[FUNCTION]
    text = bytearray(b'\xcc' * (func_rva - 0x1000 + len(code)))
    text[0:len(CALLEE_CODE)] = CALLEE_CODE
    text[8:8 + len(OTHER_CODE)] = OTHER_CODE
    text[func_rva - 0x1000:] = link(code, RELOCS, addresses, func_rva)
    for offset, value in (patch or {}).items():
        text[func_rva - 0x1000 + offset] = value
    rdata = bytearray(0x14)
    rdata[0:len(xdata)] = xdata
    struct.pack_into('<I', rdata, 0x10, 7)
    data = bytes(4)
    sections = [('.text', 0x1000, bytes(text), 0x60000020), ('.rdata', 0x2000, bytes(rdata), 0x40000040),
                ('.data', 0x3000, data, 0xC0000040)]
    if pdata:
        sections.append(('.pdata', 0x4000, struct.pack('<III', func_rva, func_rva + len(code), LAYOUT['xdata']),
                         0x40000040))
    blob = bytearray(0x400 + 0x200 * len(sections))
    blob[0:2] = b'MZ'
    struct.pack_into('<I', blob, 60, 0x40)
    blob[0x40:0x44] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', blob, 0x44, 0x8664, len(sections), 0, 0, 0, 0xF0, 0x22)
    opt = 0x58
    struct.pack_into('<H', blob, opt, 0x20B)
    struct.pack_into('<Q', blob, opt + 24, 0x140000000)
    struct.pack_into('<II', blob, opt + 32, 0x1000, 0x200)
    struct.pack_into('<II', blob, opt + 56, 0x1000 * (len(sections) + 1), 0x400)
    struct.pack_into('<H', blob, opt + 68, 3)
    struct.pack_into('<I', blob, opt + 108, 16)
    if pdata:
        struct.pack_into('<II', blob, opt + 112 + 8 * 3, 0x4000, 12)
    table = opt + 0xF0
    for i, (name, rva, content, flags) in enumerate(sections):
        raw_ptr = 0x400 + 0x200 * i
        raw_size = text_raw_size if name == '.text' and text_raw_size is not None else 0x200
        struct.pack_into('<8sIIIIIIHHI', blob, table + 40 * i, name.encode(), len(content), rva, raw_size, raw_ptr,
                         0, 0, 0, 0, flags)
        blob[raw_ptr:raw_ptr + len(content)] = content
    return bytes(blob)


def recipe(flags=('/O2', '/Gy')):
    return json.dumps({'recipe_schema': 1,
                       'compiler': {'name': 'synthetic-none', 'version': 'synthetic-0',
                                    'binary_sha256': sha256(b'synthetic compiler placeholder')},
                       'flags': list(flags)}, indent=2).encode()


def inputs(obj=None, image=None, recipe_bytes=None):
    """Return a consistent set of comparator inputs; tests then perturb exactly one of them."""
    obj = coff_object() if obj is None else obj
    image = pe_image() if image is None else image
    recipe_bytes = recipe() if recipe_bytes is None else recipe_bytes
    build_id = 'synthetic-fixture'
    revision = sha256(b'synthetic source revision')[:40]
    task = {'task_id': 'synthetic-sum', 'build_id': build_id, 'target_image_sha256': sha256(image),
            'rva': LAYOUT[FUNCTION], 'size': len(CODE), 'symbol': FUNCTION, 'source_revision': revision,
            'source_path': 'tests/synthetic/synthetic_sum.cpp', 'recipe_sha256': sha256(recipe_bytes)}
    return {
        'task': task,
        'manifest': {'schema_version': 1, 'status': 'pinned', 'build_id': build_id, 'image_sha256': sha256(image)},
        'recipe_bytes': recipe_bytes,
        'build_record': {'build_record_schema': 1, 'source_revision': revision, 'source_path': task['source_path'],
                         'recipe_sha256': sha256(recipe_bytes), 'object_sha256': sha256(obj)},
        'object_bytes': obj,
        'image_bytes': image,
        'symbol_map': {'schema': 1, 'build_id': build_id, 'folds': [],
                       'symbols': {CALLEE: {'rva': LAYOUT[CALLEE], 'size': len(CALLEE_CODE)},
                                   OTHER_CALLEE: {'rva': LAYOUT[OTHER_CALLEE], 'size': len(OTHER_CODE)},
                                   BASE: {'rva': LAYOUT[BASE], 'size': 4},
                                   COUNTER: {'rva': LAYOUT[COUNTER], 'size': 4}}},
    }
