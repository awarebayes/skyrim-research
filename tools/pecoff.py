"""Read-only x86-64 COFF object and PE32+ image parsing for the comparator.

Only the structures named in docs/comparator-contract.md are decoded. Anything outside that
subset raises Reject so the comparator fails closed instead of guessing at an encoding.
"""
import struct

MACHINE_AMD64 = 0x8664
PE32_PLUS = 0x20B

SCN_CNT_CODE = 0x00000020
SCN_CNT_UNINITIALIZED_DATA = 0x00000080
SCN_LNK_NRELOC_OVFL = 0x01000000
SCN_MEM_EXECUTE = 0x20000000

SYM_UNDEFINED = 0
SYM_ABSOLUTE = -1
SYM_DEBUG = -2
STORAGE_EXTERNAL = 2
STORAGE_STATIC = 3
TYPE_FUNCTION = 0x20

REL_AMD64 = {
    0x00: 'ABSOLUTE', 0x01: 'ADDR64', 0x02: 'ADDR32', 0x03: 'ADDR32NB', 0x04: 'REL32',
    0x05: 'REL32_1', 0x06: 'REL32_2', 0x07: 'REL32_3', 0x08: 'REL32_4', 0x09: 'REL32_5',
    0x0A: 'SECTION', 0x0B: 'SECREL', 0x0C: 'SECREL7', 0x0D: 'TOKEN', 0x0E: 'SREL32',
    0x0F: 'PAIR', 0x10: 'SSPAN32',
}

UNW_FLAG_EHANDLER = 0x1
UNW_FLAG_UHANDLER = 0x2
UNW_FLAG_CHAININFO = 0x4

EXCEPTION_DIRECTORY = 3
RUNTIME_FUNCTION_SIZE = 12


class Reject(Exception):
    """A comparison that cannot pass. `reason` is a stable code; `detail` is sanitized text.

    `raw` may hold byte-level context. It is only ever written to a private diagnostics file,
    never into the public report.
    """

    def __init__(self, reason, detail, raw=None):
        super().__init__(f'{reason}: {detail}')
        self.reason = reason
        self.detail = detail
        self.raw = raw or {}


def unpack(fmt, blob, offset, what):
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(blob):
        raise Reject('truncated-input', f'{what} extends past end of input')
    return struct.unpack_from(fmt, blob, offset)


def take(blob, offset, size, what):
    if offset < 0 or size < 0 or offset + size > len(blob):
        raise Reject('truncated-input', f'{what} extends past end of input')
    return blob[offset:offset + size]


def rel_name(kind):
    return REL_AMD64.get(kind, f'unknown-0x{kind:x}')


class Section:
    def __init__(self, index, name, vsize, vaddr, raw_size, raw_ptr, reloc_ptr, nrelocs, flags):
        self.index, self.name, self.vsize, self.vaddr = index, name, vsize, vaddr
        self.raw_size, self.raw_ptr, self.reloc_ptr, self.nrelocs, self.flags = (
            raw_size, raw_ptr, reloc_ptr, nrelocs, flags)
        self.data = None
        self.relocs = []


class Symbol:
    def __init__(self, index, name, value, section, kind, storage):
        self.index, self.name, self.value, self.section, self.kind, self.storage = (
            index, name, value, section, kind, storage)

    @property
    def is_function(self):
        return (self.kind & 0xF0) == TYPE_FUNCTION


class Reloc:
    def __init__(self, offset, symbol, kind):
        self.offset, self.symbol, self.kind = offset, symbol, kind


def read_sections(blob, table, count, strings, what):
    sections = []
    for i in range(count):
        base = table + i * 40
        raw_name, vsize, vaddr, raw_size, raw_ptr, reloc_ptr, _lines, nrelocs, _nlines, flags = unpack(
            '<8sIIIIIIHHI', blob, base, f'{what} section header {i + 1}')
        name = raw_name.rstrip(b'\0')
        if name.startswith(b'/') and strings is not None:
            if not name[1:].isdigit():
                raise Reject('unsupported-object-format', f'section {i + 1} uses an encoded long name')
            name = string_at(strings, int(name[1:]), f'section {i + 1} name')
        else:
            name = name.decode('utf-8', 'replace')
        sections.append(Section(i + 1, name, vsize, vaddr, raw_size, raw_ptr, reloc_ptr, nrelocs, flags))
    return sections


def string_at(strings, offset, what):
    if offset < 4 or offset >= len(strings):
        raise Reject('truncated-input', f'{what} points outside the string table')
    end = strings.find(b'\0', offset)
    if end < 0:
        raise Reject('truncated-input', f'{what} is not terminated')
    return strings[offset:end].decode('utf-8', 'replace')


class CoffObject:
    """A relocatable x86-64 COFF object, as a compiler emits before linking."""

    def __init__(self, blob):
        if len(blob) < 20:
            raise Reject('truncated-input', 'object header is incomplete')
        machine, nsec, _stamp, symptr, nsym, optsize, _chars = unpack('<HHIIIHH', blob, 0, 'object header')
        if machine == 0 and nsec == 0xFFFF:
            # Import objects and /bigobj objects share this signature; neither layout is decoded.
            raise Reject('unsupported-object-format', 'anonymous/bigobj object headers are not supported')
        if machine != MACHINE_AMD64:
            raise Reject('unsupported-object-format', f'object machine 0x{machine:x} is not x86-64')
        if optsize != 0:
            raise Reject('unsupported-object-format', 'object carries an optional header')
        if nsym == 0:
            raise Reject('unsupported-object-format', 'object has no symbol table')
        strtab = symptr + nsym * 18
        (strsize,) = unpack('<I', blob, strtab, 'string table size')
        if strsize < 4:
            raise Reject('unsupported-object-format', 'string table size is invalid')
        self.strings = take(blob, strtab, strsize, 'string table')
        self.sections = read_sections(blob, 20, nsec, self.strings, 'object')
        for sec in self.sections:
            if sec.flags & SCN_LNK_NRELOC_OVFL:
                raise Reject('unsupported-object-format', f'section {sec.name} uses extended relocation count')
            if sec.raw_ptr and not sec.flags & SCN_CNT_UNINITIALIZED_DATA:
                sec.data = take(blob, sec.raw_ptr, sec.raw_size, f'section {sec.name} data')
            for r in range(sec.nrelocs):
                offset, symbol, kind = unpack('<IIH', blob, sec.reloc_ptr + r * 10,
                                              f'section {sec.name} relocation {r}')
                sec.relocs.append(Reloc(offset, symbol, kind))
        self.symbols = {}
        index = 0
        while index < nsym:
            raw_name, value, section, kind, storage, naux = unpack(
                '<8sIhHBB', blob, symptr + index * 18, f'symbol {index}')
            if raw_name[:4] == b'\0\0\0\0':
                name = string_at(self.strings, struct.unpack_from('<I', raw_name, 4)[0], f'symbol {index} name')
            else:
                name = raw_name.rstrip(b'\0').decode('utf-8', 'replace')
            self.symbols[index] = Symbol(index, name, value, section, kind, storage)
            index += 1 + naux
        if index != nsym:
            raise Reject('truncated-input', 'auxiliary symbol records run past the symbol table')
        for sec in self.sections:
            for rel in sec.relocs:
                if rel.symbol not in self.symbols:
                    raise Reject('malformed-relocation', f'relocation in {sec.name} names a missing symbol')

    def section(self, number):
        if not 1 <= number <= len(self.sections):
            raise Reject('malformed-object', f'symbol refers to section {number}, which does not exist')
        return self.sections[number - 1]


class PeImage:
    """A linked PE32+ x86-64 image, addressed by RVA."""

    def __init__(self, blob):
        self.blob = blob
        if take(blob, 0, 2, 'DOS header') != b'MZ':
            raise Reject('unsupported-image-format', 'image lacks a DOS header')
        (lfanew,) = unpack('<I', blob, 60, 'DOS header')
        if take(blob, lfanew, 4, 'PE signature') != b'PE\0\0':
            raise Reject('unsupported-image-format', 'image lacks a PE signature')
        machine, nsec, _stamp, _symptr, _nsym, optsize, _chars = unpack('<HHIIIHH', blob, lfanew + 4, 'PE header')
        if machine != MACHINE_AMD64:
            raise Reject('unsupported-image-format', f'image machine 0x{machine:x} is not x86-64')
        opt = lfanew + 24
        (magic,) = unpack('<H', blob, opt, 'optional header')
        if magic != PE32_PLUS:
            raise Reject('unsupported-image-format', 'image is not PE32+')
        if optsize < 112:
            raise Reject('truncated-input', 'optional header is too short')
        (self.image_base,) = unpack('<Q', blob, opt + 24, 'optional header')
        (ndirs,) = unpack('<I', blob, opt + 108, 'optional header')
        if 112 + 8 * ndirs > optsize:
            raise Reject('truncated-input', 'data directories exceed optional header')
        self.exception_dir = (0, 0)
        if ndirs > EXCEPTION_DIRECTORY:
            self.exception_dir = unpack('<II', blob, opt + 112 + 8 * EXCEPTION_DIRECTORY, 'exception directory')
        self.sections = read_sections(blob, opt + optsize, nsec, None, 'image')
        for sec in self.sections:
            if sec.raw_size:
                take(blob, sec.raw_ptr, sec.raw_size, f'section {sec.name} data')

    def section_for(self, rva):
        for sec in self.sections:
            if sec.vaddr <= rva < sec.vaddr + max(sec.vsize, sec.raw_size):
                return sec
        raise Reject('target-range-outside-image', f'RVA 0x{rva:x} is not inside any section')

    def read(self, rva, size, what):
        sec = self.section_for(rva)
        start = rva - sec.vaddr
        extent = sec.vsize or sec.raw_size
        if start + size > extent:
            raise Reject('target-range-outside-section', f'{what} crosses the end of section {sec.name}')
        if start + size > sec.raw_size:
            # The tail of a section beyond its raw data is loader zero-fill, not file content.
            raise Reject('target-range-truncated', f'{what} extends past the raw data of section {sec.name}')
        return sec, take(self.blob, sec.raw_ptr + start, size, what)

    def runtime_functions(self):
        rva, size = self.exception_dir
        if not size:
            return []
        if size % RUNTIME_FUNCTION_SIZE:
            raise Reject('malformed-image', 'exception directory size is not a multiple of 12')
        _, table = self.read(rva, size, 'exception directory')
        return [struct.unpack_from('<III', table, i) for i in range(0, size, RUNTIME_FUNCTION_SIZE)]


def unwind_info_length(blob, what):
    """Length of the fixed UNWIND_INFO part the contract compares, after rejecting unsupported forms."""
    version_flags, _prolog, count, _frame = unpack('<BBBB', blob, 0, what)
    version, flags = version_flags & 0x7, version_flags >> 3
    if version != 1:
        raise Reject('unsupported-unwind', f'{what} has version {version}; only version 1 is decoded')
    if flags & UNW_FLAG_CHAININFO:
        raise Reject('unsupported-unwind', f'{what} is chained to another entry')
    if flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
        # Handler-specific data has a layout chosen by the handler; its length cannot be derived here.
        raise Reject('unsupported-unwind', f'{what} names an exception/termination handler')
    return 4 + 2 * (count + (count & 1))
