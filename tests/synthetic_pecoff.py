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


# ---------------------------------------------------------------------------------------------
# Contract v2 fixtures: several sections per function (funclets, handler data, chained unwind
# info, jump tables) and a small linker that places them. The layouts follow what MSVC 19.16
# emits for the original sources in tools/verifier/synthetic/eh_cases.cpp, but every byte below
# is written by hand for these tests. The linker works from the PE/COFF rules, not from
# comparator code, so a comparator mistake cannot cancel out in the fixture.

STORAGE_EXTERNAL, STORAGE_STATIC, STORAGE_LABEL = 2, 3, 6
SCN_TEXT, SCN_XDATA, SCN_RDATA8 = 0x60501020, 0x40301040, 0x40401040
IMAGE_SECTIONS = (('.text', 0x1000, 0x60000020), ('.rdata', 0x2000, 0x40000040), ('.data', 0x3000, 0xC0000040),
                  ('.pdata', 0x4000, 0x40000040))
SECTION_SPAN = 0x1000
HANDLER_THUNKS = {'__CxxFrameHandler3': 0x1100, '__C_specific_handler': 0x1110, '__GSHandlerCheck': 0x1120,
                  '__GSHandlerCheck_SEH': 0x1130, '__GSHandlerCheck_EH': 0x1140, '__CxxFrameHandler4': 0x1150}
OTHER_THUNK = 0x1160


def dwords(*values):
    return struct.pack(f'<{len(values)}I', *(v & 0xFFFFFFFF for v in values))


class Unit:
    """A relocatable object under construction, plus the placement a linker would give it."""

    def __init__(self):
        self.sections = []      # [name, bytearray, [(offset, symbol, kind)], flags]
        self.symbols = []       # (name, value, section, type, storage)

    def section(self, name, data, flags):
        self.sections.append([name, bytearray(data), [], flags])
        return len(self.sections)

    def define(self, name, section, value=0, storage=STORAGE_STATIC, function=False):
        self.symbols.append((name, value, section, 0x20 if function else 0, storage))
        return name

    def external(self, name):
        if not any(s[0] == name for s in self.symbols):
            self.symbols.append((name, 0, 0, 0, STORAGE_EXTERNAL))
        return name

    def reloc(self, section, offset, symbol, kind):
        self.sections[section - 1][2].append((offset, symbol, kind))

    def coff(self):
        strings = bytearray(4)

        def name8(name):
            raw = name.encode()
            if len(raw) <= 8:
                return raw.ljust(8, b'\0')
            offset = len(strings)
            strings.extend(raw + b'\0')
            return struct.pack('<II', 0, offset)

        index = {name: i for i, (name, *_rest) in enumerate(self.symbols)}
        header_end = 20 + 40 * len(self.sections)
        body, headers, cursor = bytearray(), bytearray(), header_end
        for name, data, rels, flags in self.sections:
            rel_ptr = cursor + len(data) if rels else 0
            headers += struct.pack('<8sIIIIIIHHI', name.encode(), 0, 0, len(data), cursor, rel_ptr, 0, len(rels), 0,
                                   flags)
            body += data
            for off, sym, kind in sorted(rels):
                body += struct.pack('<IIH', off, index[sym], kind)
            cursor = header_end + len(body)
        table = b''.join(struct.pack('<8sIhHBB', name8(n), v, s, t, c, 0) for n, v, s, t, c in self.symbols)
        struct.pack_into('<I', strings, 0, len(strings))
        header = struct.pack('<HHIIIHH', 0x8664, len(self.sections), 0, cursor, len(self.symbols), 0, 0)
        return header + bytes(headers) + bytes(body) + table + bytes(strings)

    def default_placement(self, first_code=0x1200, funclets=0x1800):
        """Code sections from `first_code` (.text$x from `funclets`), data in .rdata/.data, 16-aligned."""
        placement, cursor = {}, {'.text$mn': first_code, '.text$x': funclets, 'rdata': 0x2000, 'data': 0x3000}
        for number, (name, data, _rels, flags) in enumerate(self.sections, 1):
            if name == '.pdata':
                continue
            key = name if name in ('.text$mn', '.text$x') else ('data' if name.startswith('.data') else 'rdata')
            placement[number] = cursor[key]
            cursor[key] += (len(data) + 15) // 16 * 16
        return placement

    def link(self, externals, placement=None, drop_pdata=(), extra_pdata=(), patches=None):
        """Return a PE32+ image: sections placed, relocations applied, .pdata gathered and sorted."""
        placement = placement or self.default_placement()

        def address(symbol):
            name, value, section, _t, _c = next(s for s in self.symbols if s[0] == symbol)
            if name == '__ImageBase':
                return 0    # the linker defines it as the start of the image
            return placement[section] + value if section > 0 else externals[name]

        memory = {name: bytearray(SECTION_SPAN) for name, _rva, _f in IMAGE_SECTIONS}
        bases = {name: rva for name, rva, _f in IMAGE_SECTIONS}
        for name, rva in HANDLER_THUNKS.items():
            memory['.text'][rva - 0x1000:rva - 0x1000 + 6] = b'\xff\x25\0\0\0\0'
        memory['.text'][OTHER_THUNK - 0x1000:OTHER_THUNK - 0x1000 + 6] = b'\xff\x25\0\0\0\0'
        pdata = []
        for number, (name, data, rels, _flags) in enumerate(self.sections, 1):
            out = bytearray(data)
            if name == '.pdata':
                by_offset = {off: sym for off, sym, _k in rels}
                for base in range(0, len(data), 12):
                    entry = tuple(address(by_offset[base + k]) + struct.unpack_from('<I', data, base + k)[0]
                                  for k in (0, 4, 8))
                    if entry[0] not in drop_pdata:
                        pdata.append(entry)
                continue
            at = placement[number]
            for off, sym, kind in rels:
                addend = struct.unpack_from('<i' if kind != ADDR32NB else '<I', data, off)[0]
                if kind == ADDR32NB:
                    struct.pack_into('<I', out, off, address(sym) + addend)
                else:
                    tail = {REL32: 0, REL32_1: 1}[kind]
                    struct.pack_into('<i', out, off, address(sym) + addend - (at + off + 4 + tail))
            image_name = next(n for n, rva, _f in IMAGE_SECTIONS if rva <= at < rva + SECTION_SPAN)
            memory[image_name][at - bases[image_name]:at - bases[image_name] + len(out)] = out
        pdata = sorted(pdata + list(extra_pdata))
        memory['.pdata'][0:12 * len(pdata)] = b''.join(dwords(*e) for e in pdata)
        for rva, blob in (patches or {}).items():
            image_name = next(n for n, base, _f in IMAGE_SECTIONS if base <= rva < base + SECTION_SPAN)
            memory[image_name][rva - bases[image_name]:rva - bases[image_name] + len(blob)] = blob
        return assemble_pe([(n, rva, bytes(memory[n]), f) for n, rva, f in IMAGE_SECTIONS], (0x4000, 12 * len(pdata)))


def assemble_pe(sections, exception_dir):
    blob = bytearray(0x400 + SECTION_SPAN * len(sections))
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
    struct.pack_into('<II', blob, opt + 112 + 8 * 3, *exception_dir)
    for i, (name, rva, content, flags) in enumerate(sections):
        raw_ptr = 0x400 + SECTION_SPAN * i
        struct.pack_into('<8sIIIIIIHHI', blob, opt + 0xF0 + 40 * i, name.encode(), len(content), rva, len(content),
                         raw_ptr, 0, 0, 0, 0, flags)
        blob[raw_ptr:raw_ptr + len(content)] = content
    return bytes(blob)


def unit_inputs(unit, symbol, externals, image=None, extra_map=None, **link_args):
    """Comparator inputs for `symbol` in `unit`, linked with `externals` unless `image` is given."""
    obj = unit.coff()
    placement = unit.default_placement()
    image = unit.link(externals, placement, **link_args) if image is None else image
    name, value, section, *_ = next(s for s in unit.symbols if s[0] == symbol)
    args = inputs(obj=obj, image=image)
    args['task'].update(rva=placement[section] + value, size=len(unit.sections[section - 1][1]), symbol=symbol)
    symbols = {name: {'rva': rva, 'size': None} for name, rva in externals.items()}
    symbols.update(extra_map or {})
    args['symbol_map']['symbols'] = symbols
    return args


def image_externals(**overrides):
    externals = {CALLEE: LAYOUT[CALLEE], BASE: 0x3100, **HANDLER_THUNKS}
    externals.update(overrides)
    return externals


# --- C++ EH: one function with a try block, a typed catch, catch (...), and a destructor -----

CATCH_FUNCTION = 'SyntheticCatch'
CATCH_TYPE = '??_R0?AUSyntheticError@@@8'
CATCH_CODE = bytes.fromhex(
    '4883ec28'          # +0x00 sub  rsp, 0x28
    'e800000000'        # +0x04 call SyntheticAddOne           (REL32 at +0x05)
    'eb02'              # +0x09 jmp  +0x0d
    '33c0'              # +0x0b xor  eax, eax                   (catch continuation)
    '4883c428'          # +0x0d add  rsp, 0x28
    'c3')               # +0x11 ret
FUNCLET_CODE = bytes.fromhex(
    '4889542410'        # +0x00 mov  [rsp+0x10], rdx            (catch funclet)
    '55'                # +0x05 push rbp
    '4883ec20'          # +0x06 sub  rsp, 0x20
    '488bea'            # +0x0a mov  rbp, rdx
    '890d00000000'      # +0x0d mov  [rip+gSyntheticBase], ecx  (REL32 at +0x0f)
    '488d0500000000'    # +0x13 lea  rax, [rip+continuation]    (REL32 at +0x16)
    '4883c420'          # +0x1a add  rsp, 0x20
    '5d'                # +0x1e pop  rbp
    'c3'                # +0x1f ret
    'cc'                # +0x20 int3
    '488d8a30000000'    # +0x21 lea  rcx, [rdx+0x30]            (unwind funclet, no .pdata)
    'e900000000')       # +0x28 jmp  SyntheticAddOne            (REL32 at +0x29)
CATCH_UNWIND = bytes.fromhex('19040100' '04420000')        # EHANDLER|UHANDLER, alloc 0x28
FUNCLET_UNWIND = bytes.fromhex('190a0200' '0a320650')      # EHANDLER|UHANDLER, push rbp, alloc 0x20
TYPE_DESCRIPTOR = bytes(16) + b'.?AUSyntheticError@@\0'


def catch_unit(handler='__CxxFrameHandler3', magic=0x19930522, handler_map_tail=b'', unrelocated_action=False,
               action_to_data=False):
    u = Unit()
    f = u.section('.text$mn', CATCH_CODE, SCN_TEXT)
    x = u.section('.text$x', FUNCLET_CODE, SCN_TEXT)
    u.define(CATCH_FUNCTION, f, storage=STORAGE_EXTERNAL, function=True)
    u.define('$LN5', f, 0, STORAGE_LABEL)
    u.define('$LN3', f, 0x0B, STORAGE_LABEL)
    catch0 = u.define('?catch$0@?0??SyntheticCatch@@4HA', x, 0)
    dtor0 = u.define('?dtor$0@?0??SyntheticCatch@@4HA', x, 0x21)
    for name in (CALLEE, BASE, handler):
        u.external(name)
    u.reloc(f, 0x05, CALLEE, REL32)
    u.reloc(x, 0x0F, BASE, REL32)
    u.reloc(x, 0x16, '$LN3', REL32)
    u.reloc(x, 0x29, CALLEE, REL32)
    td = u.section('.data$r', TYPE_DESCRIPTOR, 0xC0301040)
    u.define(CATCH_TYPE, td, storage=STORAGE_EXTERNAL)

    def data_section(name, blob, flags=SCN_XDATA):
        number = u.section('.rdata' if name.startswith('$cppxdata') else '.xdata', blob, flags)
        u.define(name, number)
        return number

    funcinfo = data_section('$cppxdata$SyntheticCatch', dwords(magic, 2, 0, 1, 0, 4, 0, 0x20, 0, 1), SCN_RDATA8)
    unwind_map = data_section('$stateUnwindMap$SyntheticCatch', dwords(-1, 0, -1, 0x21 if unrelocated_action else 0))
    try_map = data_section('$tryMap$SyntheticCatch', dwords(0, 0, 1, 2, 0))
    handler_map = data_section('$handlerMap$0$SyntheticCatch',
                               dwords(8, 0, 0x28, 0, 0x38, 0x40, 0, 0, 0, 0x38) + handler_map_tail)
    ip_map = data_section('$ip2state$SyntheticCatch', dwords(0, -1, 4, 0, 9, -1, 0, 1), SCN_RDATA8)
    u.reloc(funcinfo, 0x08, '$stateUnwindMap$SyntheticCatch', ADDR32NB)
    u.reloc(funcinfo, 0x10, '$tryMap$SyntheticCatch', ADDR32NB)
    u.reloc(funcinfo, 0x18, '$ip2state$SyntheticCatch', ADDR32NB)
    u.reloc(unwind_map, 0x04, '$tryMap$SyntheticCatch' if action_to_data else dtor0, ADDR32NB)
    u.reloc(try_map, 0x10, '$handlerMap$0$SyntheticCatch', ADDR32NB)
    u.reloc(handler_map, 0x04, CATCH_TYPE, ADDR32NB)
    u.reloc(handler_map, 0x0C, catch0, ADDR32NB)
    u.reloc(handler_map, 0x20, catch0, ADDR32NB)
    for i, (sym, addend) in enumerate(((CATCH_FUNCTION, 0), (CATCH_FUNCTION, 4), (CATCH_FUNCTION, 9), (catch0, 0))):
        struct.pack_into('<I', u.sections[ip_map - 1][1], 8 * i, addend)
        u.reloc(ip_map, 8 * i, sym, ADDR32NB)
    for code_sec, label, unwind, size in ((f, '$LN5', CATCH_UNWIND, len(CATCH_CODE)), (x, catch0, FUNCLET_UNWIND, 0x21)):
        uname = f'$unwind${label}'
        xd = data_section(uname, unwind + dwords(0, 0))
        u.reloc(xd, len(unwind), handler, ADDR32NB)
        u.reloc(xd, len(unwind) + 4, '$cppxdata$SyntheticCatch', ADDR32NB)
        pd = u.section('.pdata', dwords(0, size, 0), SCN_XDATA)
        u.reloc(pd, 0, label, ADDR32NB)
        u.reloc(pd, 4, label, ADDR32NB)
        u.reloc(pd, 8, uname, ADDR32NB)
    return u


def catch_map(unit):
    """Map entries a linked catch_unit needs beyond the externals: the type descriptor."""
    placement = unit.default_placement()
    td = next(s for s in unit.symbols if s[0] == CATCH_TYPE)
    return {CATCH_TYPE: {'rva': placement[td[2]], 'size': None}}


def catch_inputs(unit=None, externals=None, **link_args):
    unit = unit or catch_unit()
    return unit_inputs(unit, CATCH_FUNCTION, externals or image_externals(), extra_map=catch_map(unit), **link_args)


def section_rva(unit, symbol):
    name, value, section, *_ = next(s for s in unit.symbols if s[0] == symbol)
    return unit.default_placement()[section] + value


# --- Chained unwind info: three .pdata entries over one section, the later two chained -------

CHAIN_FUNCTION = 'SyntheticChain'
CHAIN_CODE = bytes.fromhex(
    '85d2'              # +0x00 test edx, edx
    '7e28'              # +0x02 jle  +0x2c (early exit, before any register is saved)
    '4883ec28'          # +0x04 sub  rsp, 0x28
    '48895c2430'        # +0x08 mov  [rsp+0x30], rbx
    '8bda'              # +0x0d mov  ebx, edx
    'e800000000'        # +0x0f call SyntheticAddOne      (REL32 at +0x10)
    '03c3'              # +0x14 add  eax, ebx
    '488b5c2430'        # +0x16 mov  rbx, [rsp+0x30]
    '4883c428'          # +0x1b add  rsp, 0x28
    'c3'                # +0x1f ret
    '9090909090909090'  # +0x20 padding inside the function
    '90909090'          # +0x28
    '33c0'              # +0x2c xor  eax, eax
    'c3'                # +0x2e ret
    'cc')               # +0x2f int3
CHAIN_PRIMARY = bytes.fromhex('01040100' '04420000')               # alloc 0x28
CHAIN_SAVE = bytes.fromhex('21050100' '05340600')                  # chained; save rbx
CHAIN_EMPTY = bytes.fromhex('21000000')                            # chained, no codes


def chain_unit(second_parent='primary'):
    u = Unit()
    f = u.section('.text$mn', CHAIN_CODE, SCN_TEXT)
    u.define(CHAIN_FUNCTION, f, storage=STORAGE_EXTERNAL, function=True)
    u.define('$LN9', f, 0, STORAGE_LABEL)
    u.external(CALLEE)
    u.reloc(f, 0x10, CALLEE, REL32)
    infos = (('$unwind$SyntheticChain', CHAIN_PRIMARY, None, (0x00, 0x08)),
             ('$chain$0$SyntheticChain', CHAIN_SAVE, ('$unwind$SyntheticChain', 0x00, 0x08), (0x08, 0x20)),
             ('$chain$1$SyntheticChain', CHAIN_EMPTY, ('$unwind$SyntheticChain', 0x00, 0x08) if second_parent == 'primary'
              else ('$chain$0$SyntheticChain', 0x08, 0x20), (0x20, 0x30)))
    for name, codes, parent, (begin, end) in infos:
        blob = codes + (dwords(parent[1], parent[2], 0) if parent else b'')
        xd = u.section('.xdata', blob, SCN_XDATA)
        u.define(name, xd)
        if parent:
            u.reloc(xd, len(codes), '$LN9', ADDR32NB)
            u.reloc(xd, len(codes) + 4, '$LN9', ADDR32NB)
            u.reloc(xd, len(codes) + 8, parent[0], ADDR32NB)
        pd = u.section('.pdata', dwords(begin, end, 0), SCN_XDATA)
        u.reloc(pd, 0, '$LN9', ADDR32NB)
        u.reloc(pd, 4, '$LN9', ADDR32NB)
        u.reloc(pd, 8, name, ADDR32NB)
    return u


# --- SEH: scope table with a filter funclet and a constant handler; optional GS data --------

SEH_FUNCTION = 'SyntheticGuarded'
SEH_CODE = bytes.fromhex(
    '4883ec28'          # +0x00 sub  rsp, 0x28
    '8b01'              # +0x04 mov  eax, [rcx]            (guarded)
    'ffc0'              # +0x06 inc  eax
    'eb05'              # +0x08 jmp  +0x0f
    'b8feffffff'        # +0x0a mov  eax, -2               (handler)
    '4883c428'          # +0x0f add  rsp, 0x28
    'c3')               # +0x13 ret
FILTER_CODE = bytes.fromhex(
    '4055'              # +0x00 push rbp
    '488bea'            # +0x02 mov  rbp, rdx
    '488b01'            # +0x05 mov  rax, [rcx]
    '33c9'              # +0x08 xor  ecx, ecx
    '813805000000c0'    # +0x0a cmp  dword [rax], 0xc0000005
    '0f94c1'            # +0x11 sete cl
    '8bc1'              # +0x14 mov  eax, ecx
    '5d'                # +0x16 pop  rbp
    'c3'                # +0x17 ret
    'cc')               # +0x18 int3
FILTER_UNWIND = bytes.fromhex('01020100' '02500000')     # push rbp


def seh_unit(handler='__C_specific_handler', gs=None):
    u = Unit()
    f = u.section('.text$mn', SEH_CODE, SCN_TEXT)
    x = u.section('.text$x', FILTER_CODE, SCN_TEXT)
    u.define(SEH_FUNCTION, f, storage=STORAGE_EXTERNAL, function=True)
    u.define('$LN8', f, 0, STORAGE_LABEL)
    filt = u.define('?filt$0@?0??SyntheticGuarded@@4HA', x, 0)
    u.external(handler)
    flags = 0x19 if gs else 0x09
    scope = dwords(2, 0x04, 0x08, 0, 0x0A, 0x04, 0x08, 1, 0x0A)
    blob = bytes([flags]) + bytes.fromhex('040100' '04420000') + dwords(0) + scope + (gs or b'')
    xd = u.section('.xdata', blob, SCN_XDATA)
    u.define('$unwind$SyntheticGuarded', xd)
    u.reloc(xd, 8, handler, ADDR32NB)
    for off in (0x10, 0x14, 0x1C, 0x20, 0x24, 0x2C):
        u.reloc(xd, off, '$LN8', ADDR32NB)
    u.reloc(xd, 0x18, filt, ADDR32NB)
    pd = u.section('.pdata', dwords(0, len(SEH_CODE), 0), SCN_XDATA)
    u.reloc(pd, 0, '$LN8', ADDR32NB)
    u.reloc(pd, 4, '$LN8', ADDR32NB)
    u.reloc(pd, 8, '$unwind$SyntheticGuarded', ADDR32NB)
    fx = u.section('.xdata', FILTER_UNWIND, SCN_XDATA)
    u.define('$unwind$filt', fx)
    pd = u.section('.pdata', dwords(0, 0x19, 0), SCN_XDATA)
    u.reloc(pd, 0, filt, ADDR32NB)
    u.reloc(pd, 4, filt, ADDR32NB)
    u.reloc(pd, 8, '$unwind$filt', ADDR32NB)
    return u


# --- Jump table: a switch addressed from __ImageBase, table after the code -----------------

SWITCH_FUNCTION = 'SyntheticSwitch'
SWITCH_CODE = bytes.fromhex(
    '83f902'            # +0x00 cmp  ecx, 2
    '7717'              # +0x03 ja   +0x1c (default)
    '488d1500000000'    # +0x05 lea  rdx, [rip+__ImageBase]      (REL32 at +0x08)
    '48630a'            # +0x0c movsxd rcx, ecx (placeholder shape)
    '8b8c8a00000000'    # +0x0f mov  ecx, [rdx+rcx*4+table]      (ADDR32NB at +0x12)
    '4803ca'            # +0x16 add  rcx, rdx
    'ffe1'              # +0x19 jmp  rcx
    'cc'                # +0x1b int3
    '33c0c3'            # +0x1c default: xor eax, eax; ret
    'b801000000c3'      # +0x1f case 0
    'b802000000c3'      # +0x25 case 1
    'b803000000c3'      # +0x2b case 2
    'cccccc'            # +0x31 alignment
    '000000000000000000000000')  # +0x34 table: three ADDR32NB entries
SWITCH_TABLE = 0x34


def switch_unit():
    u = Unit()
    f = u.section('.text$mn', SWITCH_CODE, SCN_TEXT)
    u.define(SWITCH_FUNCTION, f, storage=STORAGE_EXTERNAL, function=True)
    u.define('$LN7', f, SWITCH_TABLE, STORAGE_STATIC)
    for label, at in (('$LN2', 0x1F), ('$LN3', 0x25), ('$LN4', 0x2B)):
        u.define(label, f, at, STORAGE_LABEL)
    u.external('__ImageBase')
    u.reloc(f, 0x08, '__ImageBase', REL32)
    u.reloc(f, 0x12, '$LN7', ADDR32NB)
    for i, label in enumerate(('$LN2', '$LN3', '$LN4')):
        u.reloc(f, SWITCH_TABLE + 4 * i, label, ADDR32NB)
    return u
