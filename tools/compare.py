"""Compare one compiled candidate function with a pinned target image range (contract v2).

Implements docs/comparator-contract.md. The public report holds metadata, hashes and a result
code only; byte-level context is written solely to an optional diagnostics file under .local/.
A `pass` here is evidence for review, not acceptance: it never sets a function to `matched`.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from pecoff import (EH_HANDLERS, EH_LAYOUTS, FUNCINFO_MAGIC, GS_HAS_ALIGNMENT, RUNTIME_FUNCTION_SIZE,
                    SCN_CNT_CODE, SCN_MEM_EXECUTE, STORAGE_EXTERNAL, SYM_ABSOLUTE, SYM_DEBUG, SYM_UNDEFINED,
                    TYPE_DESCRIPTOR_NAME, UNW_FLAG_CHAININFO, UNW_FLAG_EHANDLER, UNW_FLAG_UHANDLER, CoffObject,
                    PeImage, Reject, eh_size, rel_name, unwind_header)

ROOT = Path(__file__).resolve().parents[1]
COMPARATOR_VERSION = '0.4.0'
CONTRACT_VERSION = 2
REPORT_SCHEMA = 1
SHA256 = re.compile(r'[0-9a-f]{64}')
IDENT = re.compile(r'[a-z0-9][a-z0-9-]*')
# Hex runs this long in a non-hash field would most likely be leaked bytes, so they are refused.
HEX_RUN = re.compile(r'[0-9a-fA-F]{16,}')
HASH_KEYS = {'image_sha256', 'expected_image_sha256', 'object_sha256', 'code_section_sha256', 'recipe_sha256',
             'compiler_binary_sha256', 'source_sha256', 'source_revision'}

# Displacement relocations: field is a signed 32-bit offset from the end of the instruction,
# which ends `k` bytes after the 4-byte field (an immediate operand follows for k > 0).
REL32_TAIL = {0x04: 0, 0x05: 1, 0x06: 2, 0x07: 3, 0x08: 4, 0x09: 5}
ADDR32NB = 0x03
SUPPORTED_RELOCATIONS = set(REL32_TAIL) | {ADDR32NB}
# Linker-defined symbol at the start of the image; switch code addresses jump tables from it.
IMAGE_BASE = '__ImageBase'


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def comparator_source_sha256():
    digest = hashlib.sha256()
    for name in ('compare.py', 'pecoff.py'):
        digest.update(name.encode() + b'\0' + (Path(__file__).with_name(name)).read_bytes())
    return digest.hexdigest()


def need(condition, reason, detail):
    if not condition:
        raise Reject(reason, detail)


def field(mapping, key, check, reason, what):
    value = mapping.get(key) if isinstance(mapping, dict) else None
    need(check(value), reason, f'{what} field {key!r} is missing or invalid')
    return value


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def is_uint(value):
    return type(value) is int and value >= 0


def is_hash(value):
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def check_task(task):
    field(task, 'task_id', lambda v: isinstance(v, str) and IDENT.fullmatch(v), 'invalid-task', 'task')
    field(task, 'build_id', lambda v: isinstance(v, str) and IDENT.fullmatch(v), 'invalid-task', 'task')
    for key in ('target_image_sha256', 'recipe_sha256'):
        field(task, key, is_hash, 'invalid-task', 'task')
    field(task, 'rva', is_uint, 'invalid-task', 'task')
    field(task, 'size', lambda v: is_uint(v) and v > 0, 'invalid-task', 'task')
    for key in ('symbol', 'source_revision', 'source_path'):
        field(task, key, is_text, 'invalid-task', 'task')


def check_provenance(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes):
    """Every pinned input must be the one the task names before any bytes are compared."""
    need(isinstance(manifest, dict) and manifest.get('status') == 'pinned', 'target-unpinned',
         'target manifest is not pinned')
    need(manifest.get('build_id') == task['build_id'], 'manifest-mismatch', 'task build id differs from manifest')
    need(manifest.get('image_sha256') == task['target_image_sha256'], 'manifest-mismatch',
         'task image hash differs from manifest')
    need(sha256(recipe_bytes) == task['recipe_sha256'], 'stale-recipe',
         'recipe file hash differs from the recipe the task pins')
    try:
        recipe = json.loads(recipe_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Reject('invalid-recipe', 'recipe is not JSON') from None
    compiler = field(recipe, 'compiler', lambda v: isinstance(v, dict), 'invalid-recipe', 'recipe')
    field(compiler, 'binary_sha256', is_hash, 'invalid-recipe', 'recipe compiler')
    field(compiler, 'version', is_text, 'invalid-recipe', 'recipe compiler')
    field(recipe, 'flags', lambda v: isinstance(v, list) and all(is_text(f) for f in v), 'invalid-recipe', 'recipe')
    need(isinstance(build_record, dict), 'invalid-build-record', 'build record is not an object')
    need(build_record.get('source_revision') == task['source_revision'], 'stale-source-revision',
         'candidate was built from a different source revision than the task pins')
    need(build_record.get('source_path') == task['source_path'], 'source-path-mismatch',
         'candidate was built from a different source path than the task pins')
    need(build_record.get('recipe_sha256') == task['recipe_sha256'], 'stale-recipe',
         'candidate was built with a different recipe than the task pins')
    need(build_record.get('object_sha256') == sha256(object_bytes), 'object-provenance-mismatch',
         'candidate object hash differs from its build record')
    need(sha256(image_bytes) == task['target_image_sha256'], 'image-hash-mismatch',
         'target image hash differs from the pinned hash')
    return recipe


def load_symbol_map(task, symbol_map):
    need(isinstance(symbol_map, dict) and symbol_map.get('schema') == 1, 'invalid-symbol-map',
         'symbol map schema must be 1')
    need(symbol_map.get('build_id') == task['build_id'], 'symbol-map-build-mismatch',
         'symbol map belongs to another build')
    entries = symbol_map.get('symbols')
    need(isinstance(entries, dict), 'invalid-symbol-map', 'symbols must be an object')
    for name, entry in entries.items():
        need(isinstance(entry, dict) and is_uint(entry.get('rva')), 'invalid-symbol-map', 'entry needs an rva')
        need(entry.get('size') is None or (is_uint(entry['size']) and entry['size'] > 0), 'invalid-symbol-map',
             'entry size must be null or positive')
    folds = symbol_map.get('folds', [])
    need(isinstance(folds, list) and all(isinstance(g, list) and len(g) > 1 and all(n in entries for n in g)
                                         for g in folds), 'invalid-symbol-map', 'folds must list known symbols')
    for group in folds:
        need(len({entries[n]['rva'] for n in group}) == 1, 'invalid-symbol-map', 'folded symbols differ in RVA')
    return entries, [set(g) for g in folds]


def check_placement(task, entries, folds):
    """Reject symbol maps that alias or overlap the target range in ways not explicitly declared."""
    start, end, symbol = task['rva'], task['rva'] + task['size'], task['symbol']
    need(entries.get(IMAGE_BASE, {'rva': 0})['rva'] == 0, 'symbol-map-conflict',
         'symbol map places __ImageBase somewhere other than RVA 0')
    if symbol in entries:
        need(entries[symbol]['rva'] == start, 'symbol-map-conflict', 'symbol map places the function elsewhere')
        need(entries[symbol].get('size') in (None, task['size']), 'symbol-map-conflict',
             'symbol map gives the function another size')
    declared = set().union(*(g for g in folds if symbol in g)) if folds else set()
    aliases = []
    for name, entry in entries.items():
        if name in (symbol, IMAGE_BASE):
            continue
        rva, size = entry['rva'], entry.get('size')
        if rva == start:
            need(name in declared, 'undeclared-alias', 'another symbol shares the function RVA without a fold entry')
            aliases.append(name)
            continue
        overlaps = start < rva < end or (size is not None and rva < end and start < rva + size)
        need(not overlaps, 'overlapping-function', 'another symbol range overlaps the function range')
    return sorted(aliases)


def find_function(obj, name):
    matches = [s for s in obj.symbols.values() if s.name == name and s.section > 0]
    need(matches, 'function-symbol-missing', 'candidate object does not define the task symbol')
    need(len(matches) == 1, 'function-symbol-ambiguous', 'candidate object defines the task symbol twice')
    sym = matches[0]
    need(sym.storage == STORAGE_EXTERNAL, 'candidate-boundary-unsupported', 'task symbol is not external')
    sec = obj.section(sym.section)
    need(sec.flags & SCN_CNT_CODE and sec.data is not None, 'candidate-boundary-unsupported',
         'task symbol is not in an initialized code section')
    need(sym.value == 0, 'candidate-boundary-unsupported', 'function does not start its section')
    others = [s for s in obj.symbols.values() if s.section == sym.section and s.value != 0
              and (s.storage == STORAGE_EXTERNAL or s.is_function)]
    # The section end is taken as the function end, which is sound only for one function per section.
    need(not others, 'candidate-boundary-unsupported', 'code section holds more than one function')
    return sym, sec


def code_section_sha256(obj, sections):
    """SHA-256 over the function's code sections, stable across clean compiles of the same code.

    Per section, in the given order: its name, length and bytes, then each relocation sorted by
    offset as (offset, type, target symbol name). Symbol-table indices, the object time stamp and
    sections outside the list do not enter it, so recompiling or reordering the object leaves it
    unchanged while any code byte or reference target changes it.
    """
    names = {}
    for sym in obj.symbols.values():
        names[sym.name] = names.get(sym.name, 0) + 1
    digest = hashlib.sha256(b'code-section-sha256-v1\0')
    digest.update(struct.pack('<I', len(sections)))
    for sec in sections:
        name = sec.name.encode()
        digest.update(struct.pack('<II', len(name), len(sec.data)) + name + sec.data)
        relocs = sorted(sec.relocs, key=lambda r: r.offset)
        digest.update(struct.pack('<I', len(relocs)))
        for rel in relocs:
            sym = obj.symbols[rel.symbol]
            target = sym.name.encode()
            digest.update(struct.pack('<IHI', rel.offset, rel.kind, len(target)) + target)
            if names[sym.name] > 1 and sym.section > 0:
                # A name several symbols share (section symbols such as `.rdata`, repeated statics)
                # does not say which one is meant, so the target section's content identifies it.
                # Unique names add nothing here, which keeps earlier values of this hash valid.
                where = obj.section(sym.section)
                digest.update(b'@' + struct.pack('<II', sym.value, len(where.data or b''))
                              + hashlib.sha256(where.data or b'').digest())
    return digest.hexdigest()


def u32(blob, offset):
    return struct.unpack_from('<I', blob, offset)[0]


class Function:
    """Candidate sections of one function and the target RVAs they are bound to.

    The function section is bound to the task range. Funclet code and handler data are bound
    only through compared exception-data fields (see the contract), and every bound section is
    later compared in full, so a binding never stands in for a comparison.
    """

    def __init__(self, obj, func_sec, task, entries, image, coverage):
        self.obj, self.func_sec, self.task, self.entries, self.image = obj, func_sec, task, entries, image
        self.coverage, self.eh = coverage, coverage['eh']
        self.bound = {func_sec.index: task['rva']}
        self.code_ranges = [(task['rva'], task['rva'] + task['size'])]
        self.code_queue = []
        self.funclet_order = []
        self.compared_unwind = set()
        self.compared_funcinfo = set()
        self._pdata_starts = None
        self.claimed = {}
        self.consumed = {}
        self.visited = set()
        self.relocs = {sec.index: {r.offset: r for r in sec.relocs} for sec in obj.sections}

    # -- references ---------------------------------------------------------------------------

    def resolve(self, sym):
        """Target RVA of a candidate symbol (before addend), per "Mapping source symbols"."""
        if sym.section in self.bound:
            return self.bound[sym.section] + sym.value
        need(sym.section not in (SYM_ABSOLUTE, SYM_DEBUG), 'unsupported-relocation',
             'relocation targets an absolute or debug symbol')
        if sym.name == IMAGE_BASE and sym.section == SYM_UNDEFINED:
            return 0
        need(sym.name in self.entries, 'unresolved-symbol', f'no target RVA for referenced symbol {sym.name!r}')
        return self.entries[sym.name]['rva']

    def bind(self, index, rva, what):
        sec = self.obj.section(index)
        need(sec.data is not None, 'eh-data-unaccounted', f'{what} points into a section without data')
        need(rva >= 0, 'eh-reference-mismatch', f'{what} would place a section before the image')
        if sec.flags & SCN_CNT_CODE:
            # Checked at binding time: an overlapping funclet would otherwise surface only as a
            # byte mismatch in whichever range was compared first.
            end = rva + len(sec.data)
            need(all(end <= a or b <= rva for a, b in self.code_ranges), 'eh-funclet-overlap',
                 f'{what} places a funclet over the function or another funclet')
            for name, entry in self.entries.items():
                size = entry.get('size')
                need(not (rva <= entry['rva'] < end or (size and entry['rva'] < end and rva < entry['rva'] + size)),
                     'overlapping-function', f'symbol map entry {name!r} overlaps a funclet')
            self.code_ranges.append((rva, end))
            self.code_queue.append(index)
            self.funclet_order.append(index)
        else:
            self.claimed[index] = bytearray(len(sec.data))
            self.consumed[index] = set()
        self.bound[index] = rva

    def target_u32(self, rva, what):
        return u32(self.image.read(rva, 4, what)[1], 0)

    def candidate_u32(self, index, offset, what):
        data = self.obj.section(index).data
        need(data is not None and 0 <= offset and offset + 4 <= len(data), 'eh-data-unaccounted',
             f'{what} lies outside its candidate section')
        return u32(data, offset)

    def claim(self, index, offset, length, what):
        mask = self.claimed.get(index)
        need(mask is not None, 'eh-reference-kind', f'{what} is not in a bound data section')
        need(0 <= offset and offset + length <= len(mask), 'eh-data-unaccounted', f'{what} runs past its section')
        need(not any(mask[offset:offset + length]), 'eh-data-overlap', f'{what} overlaps another structure')
        mask[offset:offset + length] = b'\1' * length
        self.eh['bytes'] += length

    def int_field(self, index, offset, rva, what):
        need(offset not in self.relocs[index], 'eh-unexpected-relocation', f'{what} carries a relocation')
        value = self.candidate_u32(index, offset, what)
        if value != self.target_u32(rva, what):
            raise Reject('eh-data-mismatch', f'{what} differs',
                         raw={'field': what, 'candidate': value, 'target': self.target_u32(rva, what)})
        self.eh['int_fields'] += 1
        return value

    def ref_field(self, index, offset, rva, what, expect, reason='eh-reference-mismatch'):
        """Compare one image-relative reference; return (section, offset) of a bound target or None.

        `expect` is 'data' or 'code' for references that may bind a section of the object, and
        'external' for references resolved through the map only (handlers, type descriptors).
        """
        rel = self.relocs[index].get(offset)
        value = self.candidate_u32(index, offset, what)
        target = self.target_u32(rva, what)
        self.eh['ref_fields'] += 1
        if rel is None:
            need(value == 0, 'eh-unrelocated-reference', f'{what} is a non-zero address without a relocation')
            need(target == 0, reason, f'{what} is null in the candidate but not in the target')
            return None
        need(rel.kind == ADDR32NB, 'unsupported-relocation', f'{what} uses relocation {rel_name(rel.kind)}')
        # RVA 0 is the image header: a relocated field never legitimately encodes it, so a zero
        # target is a null the candidate does not have, not a place to bind a section.
        need(target != 0, reason, f'{what} is null in the target but not in the candidate')
        if index in self.consumed:
            self.consumed[index].add(offset)
        sym = self.obj.symbols[rel.symbol]
        if expect == 'external':
            want = self.resolve(sym) + value
            if want != target:
                raise Reject(reason, f'{what} does not encode the RVA of {sym.name!r}',
                             raw={'field': what, 'expected': want, 'target': target})
            return None
        # Every other EH reference must land in a section of this object that is (or becomes)
        # bound and is then compared in full. Resolving it through the map instead would accept
        # whatever sits at the mapped address without comparing it.
        local = sym.section > 0 and (sym.section in self.bound or sym.storage != STORAGE_EXTERNAL)
        need(local, 'eh-reference-not-local',
             f'{what} refers to {sym.name!r}, which is not a section of this object compared with the function')
        sec = self.obj.section(sym.section)
        is_code = bool(sec.flags & SCN_CNT_CODE)
        need(is_code == (expect == 'code'), 'eh-reference-kind',
             f'{what} points to a {"code" if is_code else "data"} section; expected {expect}')
        place = sym.value + value
        if sym.section in self.bound:
            if self.bound[sym.section] + place != target:
                raise Reject(reason, f'{what} does not encode the RVA of {sym.name!r}',
                             raw={'field': what, 'expected': self.bound[sym.section] + place, 'target': target})
        else:
            self.bind(sym.section, target - place, what)
        return sym.section, place

    # -- exception data -----------------------------------------------------------------------

    def structure(self, kind, index, offset, rva, what):
        """Compare one EH structure and everything it reaches; each is compared once."""
        key = (kind, index, offset)
        if key in self.visited:
            return
        self.visited.add(key)
        layout = EH_LAYOUTS[kind]
        self.claim(index, offset, eh_size(kind), what)
        values = {}
        for i, spec in enumerate(layout):
            name, form = spec[0], spec[1]
            label, at, t_at = f'{what}.{name}', offset + 4 * i, rva + 4 * i
            if form == 'int' or (form == 'code_or_int' and at not in self.relocs[index]):
                values[name] = self.int_field(index, at, t_at, label)
            elif form in ('code', 'code_or_int'):
                self.ref_field(index, at, t_at, label, 'code')
            elif form == 'type':
                self.type_field(index, at, t_at, label)
            else:
                sub, count_name = spec[2], spec[3]
                count = 1 if count_name is None else values[count_name]
                place = self.ref_field(index, at, t_at, label, 'data')
                if place is None:
                    need(count == 0 or count_name is None, 'eh-funcinfo-unsupported',
                         f'{label} is null with a non-zero count')
                    continue
                size = eh_size(sub)
                need(place[1] + count * size <= len(self.obj.section(place[0]).data), 'eh-data-unaccounted',
                     f'{label} count exceeds its candidate section')
                target_base = self.bound[place[0]] + place[1]
                for j in range(count):
                    self.structure(sub, place[0], place[1] + j * size, target_base + j * size, f'{label}[{j}]')
            if kind == 'funcinfo' and name == 'magic':
                need(values['magic'] == FUNCINFO_MAGIC, 'eh-funcinfo-unsupported',
                     'FuncInfo magic is not 0x19930522')
        structures = self.eh['structures']
        structures[kind] = structures.get(kind, 0) + 1

    def type_field(self, index, offset, rva, what):
        rel = self.relocs[index].get(offset)
        self.ref_field(index, offset, rva, what, 'external')
        if rel is None:
            return
        sym = self.obj.symbols[rel.symbol]
        if sym.section <= 0:
            return
        data = self.obj.section(sym.section).data or b''
        start = sym.value + TYPE_DESCRIPTOR_NAME + self.candidate_u32(index, offset, what)
        end = data.find(b'\0', start)
        need(start <= len(data) and end >= 0, 'eh-catch-type-mismatch', f'{what} names no type in the candidate')
        name = data[start:end + 1]
        target_at = self.resolve(sym) + start - sym.value
        if self.image.read(target_at, len(name), what)[1] != name:
            raise Reject('eh-catch-type-mismatch', f'{what} names another type in the target',
                         raw={'field': what})
        self.eh['type_names_compared'] += 1

    def gs_data(self, index, offset, rva, what):
        flags = self.int_field(index, offset, rva, f'{what}.cookie_offset')
        length = 12 if flags & GS_HAS_ALIGNMENT else 4
        if length == 12:
            self.int_field(index, offset + 4, rva + 4, f'{what}.aligned_base_offset')
            self.int_field(index, offset + 8, rva + 8, f'{what}.alignment')
        self.claim(index, offset, length, what)
        structures = self.eh['structures']
        structures['gs_data'] = structures.get('gs_data', 0) + 1
        return length

    def scope_table(self, index, offset, rva, what):
        count = self.int_field(index, offset, rva, f'{what}.count')
        self.claim(index, offset, 4, what)
        size = eh_size('scope_entry')
        need(offset + 4 + count * size <= len(self.obj.section(index).data), 'eh-data-unaccounted',
             f'{what} count exceeds its candidate section')
        for j in range(count):
            self.structure('scope_entry', index, offset + 4 + j * size, rva + 4 + j * size, f'{what}[{j}]')
        structures = self.eh['structures']
        structures['scope_table'] = structures.get('scope_table', 0) + 1
        return 4 + count * size

    def unwind_info(self, index, offset, rva, what):
        """Compare UNWIND_INFO, then its chained parent or its handler and handler data."""
        key = ('unwind', index, offset)
        if key in self.visited:
            return
        self.visited.add(key)
        self.compared_unwind.add(rva)
        data = self.obj.section(index).data
        flags, length = unwind_header(data[offset:offset + 4], f'candidate {what}')
        need(offset + length <= len(data), 'truncated-input', f'candidate {what} is truncated')
        need(not any(offset <= r < offset + length for r in self.relocs[index]), 'unsupported-relocation',
             f'candidate {what} has a relocation inside its unwind codes')
        actual = self.image.read(rva, length, f'target {what}')[1]
        if actual != data[offset:offset + length]:
            raise Reject('unwind-info-mismatch', f'{what} differs',
                         raw={'candidate': data[offset:offset + length].hex(), 'target': actual.hex()})
        self.claim(index, offset, length, what)
        self.coverage['unwind_bytes_exact'] += length
        at, t_at = offset + length, rva + length
        if flags & UNW_FLAG_CHAININFO:
            self.claim(index, at, RUNTIME_FUNCTION_SIZE, f'{what} chained entry')
            for k, part in ((0, 'begin'), (4, 'end')):
                self.ref_field(index, at + k, t_at + k, f'{what} chained {part}', 'code', 'unwind-chain-mismatch')
            parent = self.ref_field(index, at + 8, t_at + 8, f'{what} chained unwind info', 'data',
                                    'unwind-chain-mismatch')
            need(parent is not None, 'unwind-chain-mismatch', f'{what} chains to no unwind info')
            self.coverage['unwind_chained_entries'] += 1
            self.unwind_info(parent[0], parent[1], self.bound[parent[0]] + parent[1], f'{what} parent')
            return
        if not flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
            return
        rel = self.relocs[index].get(at)
        need(rel is not None and rel.kind == ADDR32NB, 'unsupported-eh-handler',
             f'{what} names a handler without an ADDR32NB relocation')
        handler = self.obj.symbols[rel.symbol]
        need(handler.section == SYM_UNDEFINED and handler.name in EH_HANDLERS, 'unsupported-eh-handler',
             f'{what} uses handler {handler.name!r}, which contract v2 does not decode')
        self.claim(index, at, 4, f'{what} handler')
        self.ref_field(index, at, t_at, f'{what} handler', 'external', 'eh-handler-mismatch')
        handlers = self.eh['handlers']
        handlers[handler.name] = handlers.get(handler.name, 0) + 1
        at, t_at = at + 4, t_at + 4
        for part in EH_HANDLERS[handler.name]:
            if part == 'funcinfo':
                self.claim(index, at, 4, f'{what} FuncInfo reference')
                place = self.ref_field(index, at, t_at, f'{what} FuncInfo', 'data')
                need(place is not None, 'eh-funcinfo-unsupported', f'{what} has a null FuncInfo')
                self.compared_funcinfo.add(self.bound[place[0]] + place[1])
                self.structure('funcinfo', place[0], place[1], self.bound[place[0]] + place[1], 'FuncInfo')
                step = 4
            elif part == 'scope_table':
                step = self.scope_table(index, at, t_at, f'{what} scope table')
            else:
                step = self.gs_data(index, at, t_at, f'{what} GS data')
            at, t_at = at + step, t_at + step

    # -- code sections ------------------------------------------------------------------------

    def pdata_entries(self, sec):
        """(begin, end, unwind section, unwind offset) for candidate .pdata entries in `sec`."""
        found = []
        for pdata in (s for s in self.obj.sections if s.name == '.pdata'):
            need(pdata.data is not None and len(pdata.data) % RUNTIME_FUNCTION_SIZE == 0, 'malformed-pdata',
                 'candidate .pdata size is not a multiple of 12')
            by_offset = self.relocs[pdata.index]
            need(all(r.kind == ADDR32NB for r in pdata.relocs), 'unsupported-relocation',
                 'candidate .pdata uses a relocation other than ADDR32NB')
            for base in range(0, len(pdata.data), RUNTIME_FUNCTION_SIZE):
                need(all(base + k in by_offset for k in (0, 4, 8)), 'malformed-pdata',
                     'candidate .pdata entry is not fully relocated')
                refs = [self.obj.symbols[by_offset[base + k].symbol] for k in (0, 4, 8)]
                addends = struct.unpack_from('<III', pdata.data, base)
                if refs[0].section != sec.index:
                    continue
                need(refs[1].section == sec.index, 'malformed-pdata', 'candidate .pdata entry ends in another section')
                need(refs[2].section > 0, 'malformed-pdata', 'candidate unwind info symbol is undefined')
                found.append((refs[0].value + addends[0], refs[1].value + addends[1], refs[2].section,
                              refs[2].value + addends[2]))
        return sorted(found)

    def compare_unwind(self, sec):
        start = self.bound[sec.index]
        end = start + len(sec.data)
        targets = []
        for begin, finish, unwind in self.image.runtime_functions():
            if begin < end and finish > start:
                need(start <= begin and finish <= end, 'unwind-entry-crosses-boundary',
                     'a target .pdata entry extends beyond the function range')
                targets.append((begin - start, finish - start, unwind))
        targets.sort()
        candidates = self.pdata_entries(sec)
        for begin, finish, *_ in candidates:
            need(0 <= begin < finish <= len(sec.data), 'malformed-pdata', 'candidate .pdata entry is outside the function')
        for side in (targets, candidates):
            spans = [(e[0], e[1]) for e in side]
            need(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'unwind-entry-overlap',
                 '.pdata entries in the range overlap or repeat')
        target_spans = [(b, f) for b, f, _ in targets]
        candidate_spans = [(b, f) for b, f, *_ in candidates]
        missing = [s for s in target_spans if s not in candidate_spans]
        extra = [s for s in candidate_spans if s not in target_spans]
        need(not missing, 'unwind-coverage-missing',
             f'{len(missing)} target .pdata entr(y/ies) in the range have no candidate counterpart')
        need(not extra, 'unwind-coverage-extra', f'{len(extra)} candidate .pdata entr(y/ies) are absent from the target')
        for (begin, _, unwind_rva), (_, _, xsec, xoff) in zip(targets, candidates):
            what = f'unwind info for the entry at +0x{begin:x}'
            if xsec in self.bound:
                need(self.bound[xsec] + xoff == unwind_rva, 'unwind-chain-mismatch',
                     f'{what} is shared differently in the target')
            else:
                need(not self.obj.section(xsec).flags & SCN_CNT_CODE, 'eh-reference-kind', f'{what} is in a code section')
                self.bind(xsec, unwind_rva - xoff, what)
            self.unwind_info(xsec, xoff, unwind_rva, what)
        self.coverage['unwind_entries'] += len(targets)
        return len(targets)

    def compare_code(self, sec, target, exact_key, reference_key):
        candidate, base = sec.data, self.bound[sec.index]
        spans = check_relocation_layout(sec, len(candidate), 'function')
        position = 0
        for start, end, rel in spans + [(len(candidate), len(candidate), None)]:
            for offset in range(position, start):
                if candidate[offset] != target[offset]:
                    where = 'code' if sec is self.func_sec else 'funclet code'
                    raise Reject('code-byte-mismatch', f'{where} differs at +0x{offset:x}',
                                 raw={'section': sec.index, 'offset': offset,
                                      'candidate': candidate[max(0, offset - 8):offset + 8].hex(),
                                      'target': target[max(0, offset - 8):offset + 8].hex()})
            self.coverage[exact_key] += start - position
            if rel is None:
                break
            ref = self.obj.symbols[rel.symbol]
            want = expected_field(rel, candidate[start:end], self.resolve(ref), base + start)
            if want != target[start:end]:
                raise Reject('relocation-target-mismatch',
                             f'{rel_name(rel.kind)} at +0x{start:x} does not encode the RVA of {ref.name!r}',
                             raw={'section': sec.index, 'offset': start, 'expected_field': want.hex(),
                                  'target_field': target[start:end].hex()})
            self.coverage[reference_key] += 4
            kinds = self.coverage['relocations_by_type']
            kinds[rel_name(rel.kind)] = kinds.get(rel_name(rel.kind), 0) + 1
            if rel.kind == ADDR32NB and ref.section == sec.index:
                self.coverage['self_rva_fields'] += 1
            position = end

    def compare_funclets(self):
        """Compare every code section the exception data bound, as the function itself is."""
        done = set()
        while self.code_queue:
            index = self.code_queue.pop(0)
            if index in done:
                continue
            done.add(index)
            sec = self.obj.section(index)
            start = self.bound[index]
            target_sec, target = self.image.read(start, len(sec.data), 'target funclet')
            need(target_sec.flags & SCN_MEM_EXECUTE, 'target-not-code', 'a funclet is not in an executable section')
            check_relocation_layout(sec, len(sec.data), 'funclet')
            self.coverage['funclet_sections'] += 1
            self.coverage['funclet_bytes_total'] += len(sec.data)
            self.compare_unwind(sec)
            self.compare_code(sec, target, 'funclet_bytes_exact', 'funclet_bytes_by_reference')
            self.check_funclet_end(sec, start + len(sec.data))

    def check_funclet_end(self, sec, end):
        """A funclet's length comes from the candidate section, so the target must show a boundary there.

        Only target-side evidence counts: a target .pdata entry or another compared code range starts
        at `end`, or the bytes from `end` to the next 16-byte boundary (at least one byte) are int3
        padding. Candidate-side facts do not: an EH reference of the candidate can point one past its
        own truncated section, and a symbol-map entry placed at the cut names nothing the target
        shows. Anything else could be the rest of a funclet the candidate truncated, so it is rejected.
        """
        known = self.pdata_starts() | {a for a, _ in self.code_ranges}
        if end in known:
            return
        pad = (-end) % 16 or 1
        try:
            following = self.image.read(end, pad, 'bytes after a funclet')[1]
        except Reject:
            following = b''
        need(following and all(b == 0xCC for b in following), 'eh-funclet-extent',
             f'the target continues after funclet section #{sec.index} without padding or a known start')

    def pdata_starts(self):
        if self._pdata_starts is None:
            self._pdata_starts = {b for b, _e, _u in self.image.runtime_functions()}
        return self._pdata_starts

    def check_target_closure(self):
        """No target .pdata entry outside the compared code may belong to this function.

        A chained entry whose chain reaches an unwind info compared here, or a handler entry whose
        C++ handler data names a FuncInfo compared here, is part of this function that the
        candidate does not have (for example a candidate cut at a chained-entry boundary).
        """
        funcinfo_handlers = {self.entries[name]['rva'] for name, layout in EH_HANDLERS.items()
                             if layout[0] == 'funcinfo' and name in self.entries}
        for begin, _end, unwind in self.image.runtime_functions():
            if any(a <= begin < b for a, b in self.code_ranges):
                continue
            current = unwind
            for _depth in range(64):
                try:
                    head = self.image.read(current, 4, 'target unwind info')[1]
                except Reject:
                    break
                flags, count = head[0] >> 3, head[2]
                length = 4 + 2 * (count + (count & 1))
                try:
                    if flags & UNW_FLAG_CHAININFO:
                        parent = self.target_u32(current + length + 8, 'target chained entry')
                        need(parent not in self.compared_unwind, 'unwind-chain-outside',
                             'a target .pdata entry outside the compared code chains to this function')
                        current = parent
                        continue
                    if flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER) and \
                            self.target_u32(current + length, 'target handler') in funcinfo_handlers:
                        need(self.target_u32(current + length + 4, 'target handler data') not in self.compared_funcinfo,
                             'eh-funclet-outside',
                             'a target .pdata entry outside the compared code uses this function\'s FuncInfo')
                except Reject as exc:
                    if exc.reason in ('unwind-chain-outside', 'eh-funclet-outside'):
                        raise
                break

    def check_complete(self):
        """Every bound data section must be fully claimed and its relocations all consumed."""
        for index, mask in self.claimed.items():
            sec = self.obj.section(index)
            need(all(mask), 'eh-data-unaccounted',
                 f'{mask.count(0)} byte(s) of candidate section {sec.name} #{index} are not part of any decoded structure')
            unused = set(self.relocs[index]) - self.consumed[index]
            need(not unused, 'eh-data-unaccounted',
                 f'{len(unused)} relocation(s) in candidate section {sec.name} #{index} were not compared')


def check_relocation_layout(sec, size, what):
    spans = []
    for rel in sorted(sec.relocs, key=lambda r: r.offset):
        need(rel.kind in SUPPORTED_RELOCATIONS, 'unsupported-relocation',
             f'{what} uses relocation {rel_name(rel.kind)} at +0x{rel.offset:x}')
        need(rel.offset + 4 <= size, 'malformed-relocation', f'{what} relocation at +0x{rel.offset:x} is out of range')
        need(not spans or spans[-1][1] <= rel.offset, 'malformed-relocation', f'{what} relocations overlap')
        spans.append((rel.offset, rel.offset + 4, rel))
    return spans


def expected_field(rel, addend_bytes, target_rva, place_rva):
    if rel.kind == ADDR32NB:
        value = target_rva + struct.unpack('<I', addend_bytes)[0]
        need(value <= 0xFFFFFFFF, 'relocation-overflow', f'ADDR32NB at +0x{rel.offset:x} overflows')
        return struct.pack('<I', value)
    value = target_rva + struct.unpack('<i', addend_bytes)[0] - (place_rva + 4 + REL32_TAIL[rel.kind])
    need(-2**31 <= value < 2**31, 'relocation-overflow', f'{rel_name(rel.kind)} at +0x{rel.offset:x} overflows')
    return struct.pack('<i', value)


def sanitized(report):
    """Raise if any report string looks like leaked bytes; hashes are allowed only in hash fields."""
    def walk(value, key=''):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, (bytes, bytearray)):
            raise ValueError(f'report field {key!r} holds raw bytes')
        elif isinstance(value, str):
            if key in HASH_KEYS:
                return
            if HEX_RUN.search(value):
                raise ValueError(f'report field {key!r} holds a long hex run')
    walk(report)
    return report


def write_diagnostics(path, private_root, report, raw):
    path, private_root = Path(path).resolve(), Path(private_root).resolve()
    if private_root not in path.parents:
        raise Reject('diagnostics-path-not-private', 'diagnostics must be written under the private root')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'report': report, 'raw': raw}, indent=2) + '\n')


def compare(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes, symbol_map,
            diagnostics=None, private_root=ROOT / '.local'):
    """Return a sanitized report dict. Never raises for comparison failures; they become `fail`."""
    coverage = {'code_bytes_total': None, 'code_bytes_exact': 0, 'code_bytes_by_reference': 0,
                'relocations_by_type': {}, 'self_rva_fields': 0, 'unwind_entries': 0, 'unwind_chained_entries': 0,
                'unwind_bytes_exact': 0, 'unwind': 'not-checked', 'aliases_declared': [],
                'funclet_sections': 0, 'funclet_bytes_total': 0, 'funclet_bytes_exact': 0,
                'funclet_bytes_by_reference': 0,
                'eh': {'handlers': {}, 'structures': {}, 'ref_fields': 0, 'int_fields': 0, 'bytes': 0,
                       'type_names_compared': 0}}
    report = {'report_schema': REPORT_SCHEMA, 'contract_version': CONTRACT_VERSION,
              'comparator': {'version': COMPARATOR_VERSION, 'source_sha256': comparator_source_sha256()},
              'acceptance': 'not-evaluated', 'result': 'fail', 'reason': None, 'detail': None}
    raw = {}
    obj = sec = function = None
    try:
        check_task(task)
        report.update(task_id=task['task_id'],
                      function={'build_id': task['build_id'], 'rva': task['rva'], 'size': task['size'],
                                'symbol': task['symbol']},
                      source={'source_revision': task['source_revision'], 'path': task['source_path']},
                      target={'expected_image_sha256': task['target_image_sha256'],
                              'image_sha256': sha256(image_bytes)},
                      candidate={'object_sha256': sha256(object_bytes)})
        recipe = check_provenance(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes)
        report['recipe'] = {'recipe_sha256': task['recipe_sha256'],
                            'compiler_binary_sha256': recipe['compiler']['binary_sha256'],
                            'compiler_version': recipe['compiler']['version'], 'flags': recipe['flags']}
        entries, folds = load_symbol_map(task, symbol_map)
        coverage['aliases_declared'] = check_placement(task, entries, folds)
        obj, image = CoffObject(object_bytes), PeImage(image_bytes)
        _, sec = find_function(obj, task['symbol'])
        need(len(sec.data) == task['size'], 'function-size-mismatch',
             f'candidate function is {len(sec.data)} bytes; task range is {task["size"]} bytes')
        target_sec, target = image.read(task['rva'], task['size'], 'target function range')
        need(target_sec.flags & SCN_MEM_EXECUTE, 'target-not-code', 'target range is not in an executable section')
        coverage['code_bytes_total'] = task['size']
        check_relocation_layout(sec, len(sec.data), 'function')
        function = Function(obj, sec, task, entries, image, coverage)
        primary_entries = function.compare_unwind(sec)
        function.compare_code(sec, target, 'code_bytes_exact', 'code_bytes_by_reference')
        function.compare_funclets()
        function.check_complete()
        function.check_target_closure()
        coverage['unwind'] = 'covered' if primary_entries else 'none-in-range'
        need(coverage['code_bytes_exact'] + coverage['code_bytes_by_reference'] == task['size'], 'coverage-gap',
             'not every function byte was compared')
        need(coverage['funclet_bytes_exact'] + coverage['funclet_bytes_by_reference'] == coverage['funclet_bytes_total'],
             'coverage-gap', 'not every funclet byte was compared')
        report.update(result='pass', reason='all-checks-passed', detail='all contract v2 checks passed')
    except Reject as exc:
        report.update(reason=exc.reason, detail=exc.detail)
        raw = exc.raw
    if sec is not None:
        # Function section first, then funclets in the order the exception data reached them.
        funclets = [obj.section(i) for i in function.funclet_order] if function is not None else []
        report['candidate']['code_section_sha256'] = code_section_sha256(obj, [sec] + funclets)
        report['candidate']['code_sections'] = 1 + len(funclets)
    report['coverage'] = coverage
    sanitized(report)
    if diagnostics is not None:
        write_diagnostics(diagnostics, private_root, report, raw)
    return report


def load_json(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, type=Path, help='Task JSON pinning function, source and recipe')
    parser.add_argument('--manifest', default=ROOT / 'builds/target.json', type=Path)
    parser.add_argument('--recipe', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    parser.add_argument('--object', required=True, type=Path, help='Candidate COFF object')
    parser.add_argument('--image', required=True, type=Path, help='Pinned target PE32+ image')
    parser.add_argument('--symbols', required=True, type=Path, help='Symbol-to-RVA map for the target build')
    parser.add_argument('--report', type=Path, help='Write the sanitized report here instead of stdout')
    parser.add_argument('--diagnostics', type=Path, help='Private diagnostics path; must be under .local/')
    args = parser.parse_args()
    try:
        report = compare(load_json(args.task), load_json(args.manifest), args.recipe.read_bytes(),
                         load_json(args.build_record), args.object.read_bytes(), args.image.read_bytes(),
                         load_json(args.symbols), diagnostics=args.diagnostics)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f'FAIL: cannot read inputs: {exc}', file=sys.stderr)
        return 2
    except Reject as exc:
        print(f'FAIL: {exc.reason}: {exc.detail}', file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(text)
    else:
        sys.stdout.write(text)
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
