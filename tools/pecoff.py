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
TLS_DIRECTORY = 9
RUNTIME_FUNCTION_SIZE = 12
TLS_DIRECTORY64_SIZE = 40


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
        self.tls_dir = (0, 0)
        if ndirs > TLS_DIRECTORY:
            self.tls_dir = unpack('<II', blob, opt + 112 + 8 * TLS_DIRECTORY, 'TLS directory')
        self._tls = None
        self._funclet_entries = {}
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

    def tls_template(self):
        """(start RVA, end RVA, index-slot RVA) of the TLS template, validated as the contract states.

        The MSVC linker writes a SECREL against a thread-local symbol as its offset from the
        template start, also when it merges the template into another section at a non-zero
        offset (measured), so offsets are taken from the template start. The template must lie
        in one section, as a linked template does.
        """
        if self._tls is not None:
            return self._tls
        rva, size = self.tls_dir
        if not rva:
            raise Reject('tls-directory-missing', 'the image has no TLS directory')
        if size < TLS_DIRECTORY64_SIZE:
            raise Reject('malformed-tls-directory', 'TLS directory is shorter than IMAGE_TLS_DIRECTORY64')
        try:
            _, raw = self.read(rva, TLS_DIRECTORY64_SIZE, 'TLS directory')
        except Reject as exc:
            raise Reject('malformed-tls-directory', f'TLS directory is not readable ({exc.reason})') from None
        start_va, end_va, index_va = struct.unpack_from('<QQQ', raw, 0)
        start, end, index = start_va - self.image_base, end_va - self.image_base, index_va - self.image_base
        if not (0 <= start <= end and index >= 0):
            raise Reject('malformed-tls-directory', 'TLS template bounds or index slot lie outside the image')
        try:
            self.section_for(index)
            sec = self.section_for(start)
        except Reject:
            raise Reject('malformed-tls-directory', 'TLS template or index slot is not inside a section') from None
        if end > sec.vaddr + max(sec.vsize, sec.raw_size):
            raise Reject('unsupported-tls-layout', f'TLS template runs past the end of section {sec.name}')
        self._tls = (start, end, index)
        return self._tls

    def runtime_functions(self):
        rva, size = self.exception_dir
        if not size:
            return []
        if size % RUNTIME_FUNCTION_SIZE:
            raise Reject('malformed-image', 'exception directory size is not a multiple of 12')
        _, table = self.read(rva, size, 'exception directory')
        return [struct.unpack_from('<III', table, i) for i in range(0, size, RUNTIME_FUNCTION_SIZE)]

    def funclet_entries(self, handler_rvas):
        """{code RVA: set of FuncInfo RVAs} for every funclet entry a FuncInfo in the image names.

        A funclet entry is the action of an unwind-map entry or the handler of a catch entry: the
        address the C++ EH runtime calls, so code starts there. IP-to-state addresses are not
        entries (they mark state changes inside code) and are left out. FuncInfos are found
        through `.pdata` entries whose unwind info names a handler in `handler_rvas`, the handlers
        whose data starts with a FuncInfo RVA. A FuncInfo that is not version 0x19930522 or cannot
        be read whole adds nothing, so a damaged one can only withhold evidence, never add it.
        """
        key = frozenset(handler_rvas)
        if key in self._funclet_entries:
            return self._funclet_entries[key]
        out, seen = {}, set()
        for _begin, _end, unwind in self.runtime_functions() if key else ():
            try:
                head = self.read(unwind, 4, 'unwind info')[1]
                flags, count = head[0] >> 3, head[2]
                if head[0] & 0x7 != 1 or flags & UNW_FLAG_CHAININFO or not flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
                    continue
                at = unwind + 4 + 2 * (count + (count & 1))
                handler, funcinfo = struct.unpack('<II', self.read(at, 8, 'handler and data')[1])
                if handler not in key or funcinfo in seen:
                    continue
                seen.add(funcinfo)
                found = self.funcinfo_entries(funcinfo)
            except Reject:
                continue
            for rva in found:
                out.setdefault(rva, set()).add(funcinfo)
        self._funclet_entries[key] = out
        return out

    def funcinfo_entries(self, funcinfo):
        """Funclet entry RVAs one FuncInfo names; raises Reject if any part of it is unreadable."""
        fields = struct.unpack('<10I', self.read(funcinfo, 40, 'FuncInfo')[1])
        magic, max_state, unwind_map, n_try, try_map = fields[:5]
        if magic != FUNCINFO_MAGIC:
            raise Reject('eh-funcinfo-unsupported', 'FuncInfo magic is not 0x19930522')
        found = set()
        if max_state:
            table = self.read(unwind_map, 8 * max_state, 'unwind map')[1]
            found |= {struct.unpack_from('<I', table, 8 * i + 4)[0] for i in range(max_state)}
        if n_try:
            tries = self.read(try_map, 20 * n_try, 'try-block map')[1]
            for t in range(n_try):
                n_catch, handlers = struct.unpack_from('<II', tries, 20 * t + 12)
                if n_catch:
                    table = self.read(handlers, 20 * n_catch, 'handler array')[1]
                    found |= {struct.unpack_from('<I', table, 20 * c + 12)[0] for c in range(n_catch)}
        # A null action (a state without cleanup) names no code.
        found.discard(0)
        return found


def unwind_header(blob, what):
    """Return (flags, length of header plus codes) for a version 1 UNWIND_INFO.

    The length includes the padding slot that keeps an odd code count 4-byte aligned; whatever
    follows (handler RVA and data, or a chained RUNTIME_FUNCTION) depends on the flags.
    """
    version_flags, _prolog, count, _frame = unpack('<BBBB', blob, 0, what)
    version, flags = version_flags & 0x7, version_flags >> 3
    if version != 1:
        raise Reject('unsupported-unwind', f'{what} has version {version}; only version 1 is decoded')
    if flags & UNW_FLAG_CHAININFO and flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
        raise Reject('unsupported-unwind', f'{what} combines a chain with a handler')
    return flags, 4 + 2 * (count + (count & 1))


# Language-specific handlers whose data layout contract v2 decodes, by the name the object
# references. The value names the layout of the data that follows the handler RVA.
EH_HANDLERS = {
    '__CxxFrameHandler3': ('funcinfo',),
    '__GSHandlerCheck_EH': ('funcinfo', 'gs'),
    '__C_specific_handler': ('scope_table',),
    '__GSHandlerCheck_SEH': ('scope_table', 'gs'),
    '__GSHandlerCheck': ('gs',),
}
FUNCINFO_MAGIC = 0x19930522
GS_HAS_ALIGNMENT = 0x4

# x64 C++ EH structures as MSVC 19.16 emits them; every field is 4 bytes. Field kinds:
#   int          compared as a value; no relocation may fall on it
#   code         image-relative address of code (null allowed where MSVC leaves it empty)
#   type         image-relative address of a TypeDescriptor, null for catch (...)
#   code_or_int  scope-table handler/target: an address when relocated, otherwise a constant
#   array        image-relative address of `count` consecutive structures of another kind;
#                `count` names an earlier field, or None for exactly one structure
EH_LAYOUTS = {
    'funcinfo': (('magic', 'int'), ('max_state', 'int'),
                 ('unwind_map', 'array', 'unwind_map_entry', 'max_state'), ('n_try_blocks', 'int'),
                 ('try_block_map', 'array', 'try_block', 'n_try_blocks'), ('n_ip_map', 'int'),
                 ('ip_to_state_map', 'array', 'ip_to_state', 'n_ip_map'), ('unwind_help', 'int'),
                 ('es_type_list', 'array', 'es_type_list', None), ('eh_flags', 'int')),
    'unwind_map_entry': (('to_state', 'int'), ('action', 'code')),
    'try_block': (('try_low', 'int'), ('try_high', 'int'), ('catch_high', 'int'), ('n_catches', 'int'),
                  ('handler_array', 'array', 'handler_type', 'n_catches')),
    'handler_type': (('adjectives', 'int'), ('type_descriptor', 'type'), ('catch_object', 'int'),
                     ('handler', 'code'), ('frame', 'int')),
    'ip_to_state': (('ip', 'code'), ('state', 'int')),
    'es_type_list': (('n_types', 'int'), ('types', 'array', 'handler_type', 'n_types')),
    'scope_entry': (('begin', 'code'), ('end', 'code'), ('handler', 'code_or_int'),
                    ('jump_target', 'code_or_int')),
}
# A TypeDescriptor is a vtable pointer and a spare pointer, then the decorated name.
TYPE_DESCRIPTOR_NAME = 16


def eh_size(kind):
    return 4 * len(EH_LAYOUTS[kind])
