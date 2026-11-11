"""Walk the exception data of every function in a PE32+ image with the comparator v2 layouts.

There is no candidate here, so nothing is compared: the walk shows whether contract v2 can
decode each function's unwind chain, handler and handler data completely, and why not where it
cannot. Output is counts only (no bytes, no addresses), so it is safe to read back for the
pinned image under G2.

Handlers are named by their RVA. Import thunks (`jmp [__imp_X]`) are named after the import.
A handler the image defines itself has no name in the image; its layout is inferred from its
data, and the output says so:
  - first dword of every use points at FuncInfo magic 0x19930522 -> `__GSHandlerCheck_EH`
  - otherwise every use parses as a scope table followed by GS data -> `__GSHandlerCheck_SEH`
  - otherwise every use parses as GS data alone -> `__GSHandlerCheck`

    python3 tools/verifier/eh_census.py <image> [--sample verdicts.tsv]

`--sample` takes the survey's verdicts file (rva, size, verdict, reasons columns) and adds the
supported share of that sample before and after v2.
"""
import argparse
import collections
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pecoff import (EH_HANDLERS, EH_LAYOUTS, FUNCINFO_MAGIC, GS_HAS_ALIGNMENT, SCN_MEM_EXECUTE,  # noqa: E402
                    UNW_FLAG_CHAININFO, UNW_FLAG_EHANDLER, UNW_FLAG_UHANDLER, PeImage, Reject, eh_size)

# Arrays longer than this are treated as malformed rather than walked.
MAX_COUNT = 4096
# Survey reasons contract v2 lifts when the census accounts for the function's EH data/chain.
LIFTED = {'exception-handler', 'chained-unwind', 'multiple-pdata', 'jump-table'}


class Fail(Exception):
    pass


class Image:
    def __init__(self, blob):
        self.blob, self.pe = blob, PeImage(blob)
        self.entries = self.pe.runtime_functions()
        self.by_begin = {b: (b, e, u) for b, e, u in self.entries}
        self.imports = self._imports()

    def u32(self, rva):
        try:
            return struct.unpack('<I', self.pe.read(rva, 4, 'eh field')[1])[0]
        except Reject:
            raise Fail('rva-outside-image') from None

    def byte(self, rva):
        try:
            return self.pe.read(rva, 1, 'eh field')[1][0]
        except Reject:
            raise Fail('rva-outside-image') from None

    def is_code(self, rva):
        try:
            return bool(self.pe.section_for(rva).flags & SCN_MEM_EXECUTE)
        except Reject:
            return False

    def _imports(self):
        lfanew = struct.unpack_from('<I', self.blob, 60)[0]
        imp_rva, imp_size = struct.unpack_from('<II', self.blob, lfanew + 24 + 112 + 8)
        names = {}
        if not imp_size:
            return names
        d = imp_rva
        while True:
            olt, _, _, name, ft = struct.unpack('<IIIII', self.pe.read(d, 20, 'import')[1])
            if not ft:
                return names
            i, src = 0, olt or ft
            while True:
                (e,) = struct.unpack('<Q', self.pe.read(src + 8 * i, 8, 'import')[1])
                if not e:
                    break
                if not e >> 63:
                    names[ft + 8 * i] = self.cstr((e & 0x7FFFFFFF) + 2)
                i += 1
            d += 20

    def cstr(self, rva):
        out = bytearray()
        while (c := self.byte(rva)) != 0:
            out.append(c)
            rva += 1
        return out.decode('ascii', 'replace')

    def unwind(self, rva):
        """(flags, length of header and codes) or Fail."""
        head = self.byte(rva)
        if head & 7 != 1:
            raise Fail('unwind-version')
        flags, count = head >> 3, self.byte(rva + 2)
        if flags & UNW_FLAG_CHAININFO and flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
            raise Fail('chain-with-handler')
        return flags, 4 + 2 * (count + (count & 1))

    def thunk_target(self, rva):
        try:
            code = self.pe.read(rva, 6, 'thunk')[1]
        except Reject:
            return None
        if code[:2] == b'\xff\x25':
            return self.imports.get(rva + 6 + struct.unpack('<i', code[2:])[0])
        return None


class Walker:
    """Target-only walk of one handler's data with the comparator's layouts."""

    def __init__(self, img):
        self.img = img

    def structure(self, kind, rva, seen, counts, code_refs):
        if (kind, rva) in seen:
            return
        seen.add((kind, rva))
        counts[kind] += 1
        values = {}
        for i, spec in enumerate(EH_LAYOUTS[kind]):
            name, form = spec[0], spec[1]
            value = self.img.u32(rva + 4 * i)
            if form == 'int':
                values[name] = value
                if kind == 'funcinfo' and name == 'magic' and value != FUNCINFO_MAGIC:
                    raise Fail('funcinfo-magic')
            elif form in ('code', 'code_or_int'):
                if value and (form == 'code' or value > 0xFF):
                    if not self.img.is_code(value):
                        raise Fail('code-reference-not-code')
                    code_refs.append((kind, name, value))
            elif form == 'type':
                if value:
                    self.img.u32(value)
            else:
                count = 1 if spec[3] is None else values[spec[3]]
                if not value:
                    if count and spec[3] is not None:
                        raise Fail('null-array-with-count')
                    continue
                if count > MAX_COUNT:
                    raise Fail('count-implausible')
                for j in range(count):
                    self.structure(spec[2], value + j * eh_size(spec[2]), seen, counts, code_refs)

    def handler_data(self, layout, rva, counts, code_refs, seen):
        for part in layout:
            if part == 'funcinfo':
                self.structure('funcinfo', self.img.u32(rva), seen, counts, code_refs)
                rva += 4
            elif part == 'scope_table':
                count = self.img.u32(rva)
                if count > MAX_COUNT:
                    raise Fail('count-implausible')
                counts['scope_table'] += 1
                for j in range(count):
                    self.structure('scope_entry', rva + 4 + 16 * j, seen, counts, code_refs)
                rva += 4 + 16 * count
            else:
                flags = self.img.u32(rva)
                counts['gs_data'] += 1
                rva += 12 if flags & GS_HAS_ALIGNMENT else 4


def handler_names(img):
    """Name every handler RVA used in the image: import thunks by import, local ones by inference."""
    uses = collections.defaultdict(list)
    for begin, end, unwind in img.entries:
        try:
            flags, length = img.unwind(unwind)
        except Fail:
            continue
        if flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
            uses[img.u32(unwind + length)].append(unwind + length + 4)
    names, inferred = {}, {}
    walker = Walker(img)
    for handler, datas in uses.items():
        imported = img.thunk_target(handler)
        if imported:
            names[handler] = imported
            continue
        for candidate in ('__GSHandlerCheck_EH', '__GSHandlerCheck_SEH', '__GSHandlerCheck'):
            ok = 0
            for data in datas:
                try:
                    if candidate == '__GSHandlerCheck_EH' and img.u32(img.u32(data)) != FUNCINFO_MAGIC:
                        continue
                    if candidate == '__GSHandlerCheck':
                        flags = img.u32(data)
                        if flags & ~0x7 > 0x100000:
                            continue
                    walker.handler_data(EH_HANDLERS[candidate], data, collections.Counter(), [], set())
                    ok += 1
                except Fail:
                    pass
            if ok == len(datas):
                names[handler] = candidate
                inferred[candidate] = inferred.get(candidate, 0) + len(datas)
                break
        else:
            names[handler] = 'unidentified-local-handler'
    return names, inferred, {names[h]: len(d) for h, d in uses.items()}


def function_census(img, names, rva):
    """Decode one function; return (reasons, extent end, facts)."""
    facts = collections.Counter()
    primary = img.by_begin.get(rva)
    if primary is None:
        return ['no-pdata-at-entry'], None, facts
    walker = Walker(img)
    try:
        flags, _ = img.unwind(primary[2])
        if flags & UNW_FLAG_CHAININFO:
            return ['entry-is-chained'], None, facts
        # Chained entries that follow contiguously and lead back to this primary are its body.
        members, end = [primary], primary[1]
        while end in img.by_begin:
            entry = img.by_begin[end]
            root, steps = entry, 0
            while True:
                f, length = img.unwind(root[2])
                if not f & UNW_FLAG_CHAININFO:
                    break
                parent = tuple(img.u32(root[2] + length + k) for k in (0, 4, 8))
                if parent not in img.entries_set:
                    raise Fail('chain-parent-not-an-entry')
                root, steps = parent, steps + 1
                if steps > 64:
                    raise Fail('chain-loop')
            if root != primary or entry is primary:
                break
            members.append(entry)
            end = entry[1]
        facts['entries'] = len(members)
        facts['chained'] = len(members) - 1
        # A chained entry elsewhere whose root is this primary would be a split body.
        if any(e[0] >= end or e[0] < rva for e in img.chain_children.get(primary, [])):
            raise Fail('chained-part-outside-section')
        seen, code_refs = set(), []
        for entry in members:
            f, length = img.unwind(entry[2])
            if f & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
                name = names.get(img.u32(entry[2] + length), 'unknown')
                if name not in EH_HANDLERS:
                    raise Fail('unsupported-handler:' + name)
                facts['handler:' + name] += 1
                walker.handler_data(EH_HANDLERS[name], entry[2] + length + 4, facts, code_refs, seen)
        # Funclets: catch handlers, unwind actions, filters and __finally blocks must be code; the
        # ones with their own .pdata get their unwind (and handler) walked too.
        for kind, field, target in code_refs:
            if kind in ('unwind_map_entry', 'handler_type', 'scope_entry') and field in ('action', 'handler'):
                facts['funclet_refs'] += 1
                entry = img.by_begin.get(target)
                if entry:
                    f, length = img.unwind(entry[2])
                    if f & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
                        name = names.get(img.u32(entry[2] + length), 'unknown')
                        if name not in EH_HANDLERS:
                            raise Fail('unsupported-handler:' + name)
                        walker.handler_data(EH_HANDLERS[name], entry[2] + length + 4, facts, [], seen)
        return [], end, facts
    except Fail as exc:
        return [str(exc)], None, facts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('image')
    parser.add_argument('--sample', help='survey verdicts.tsv to report the supported share for')
    args = parser.parse_args()
    img = Image(Path(args.image).read_bytes())
    img.entries_set = set(img.entries)
    children = collections.defaultdict(list)
    for entry in img.entries:
        try:
            f, length = img.unwind(entry[2])
        except Fail:
            continue
        if f & UNW_FLAG_CHAININFO:
            root = entry
            for _ in range(64):
                f, length = img.unwind(root[2])
                if not f & UNW_FLAG_CHAININFO:
                    break
                root = tuple(img.u32(root[2] + length + k) for k in (0, 4, 8))
            children[root].append(entry)
    img.chain_children = children
    names, inferred, uses = handler_names(img)
    out = {'pdata_entries': len(img.entries), 'handler_uses_by_name': uses, 'local_handlers_inferred': inferred}

    primaries = [b for b, e, u in img.entries if not img.unwind(u)[0] & UNW_FLAG_CHAININFO] \
        if all(img.byte(u) & 7 == 1 for _b, _e, u in img.entries) else None
    if primaries is None:
        primaries = []
        for b, e, u in img.entries:
            try:
                if not img.unwind(u)[0] & UNW_FLAG_CHAININFO:
                    primaries.append(b)
            except Fail:
                primaries.append(b)
    by_kind, reasons, structures = collections.Counter(), collections.Counter(), collections.Counter()
    funclet_starts = set()
    for b in primaries:
        r, _end, facts = function_census(img, names, b)
        kind = next((k[8:] for k in facts if k.startswith('handler:')), 'none')
        if facts['chained']:
            kind += '+chained'
        by_kind[(kind, 'accounted' if not r else 'not-accounted')] += 1
        for reason in r:
            reasons[reason] += 1
        for k, v in facts.items():
            if not k.startswith('handler:') and k not in ('entries', 'chained', 'funclet_refs'):
                structures[k] += v
    out['primary_entries'] = len(primaries)
    out['by_handler_kind'] = {f'{k} {s}': v for (k, s), v in sorted(by_kind.items())}
    out['not_accounted_reasons'] = dict(reasons.most_common())
    out['structures_walked'] = dict(structures)

    if args.sample:
        rows = [line.split('\t') for line in Path(args.sample).read_text().splitlines()[1:] if line.strip()]
        before = after = 0
        bytes_total = bytes_before = bytes_after = bytes_after_extent = 0
        remaining, lifted_by = collections.Counter(), collections.Counter()
        for row in rows:
            rva, size, verdict, survey_reasons = int(row[0], 16), row[1], row[2], row[3]
            size = int(size) if size.isdigit() else 0
            reasons_v1 = set() if survey_reasons == '-' else set(survey_reasons.split(','))
            bytes_total += size
            if not reasons_v1:
                before += 1
                bytes_before += size
            r, end, facts = function_census(img, names, rva) if rva in img.by_begin else ([], None, {})
            eh_ok = not r
            left = {x for x in reasons_v1 if not (x in LIFTED and eh_ok)}
            if not left:
                after += 1
                bytes_after += size
                bytes_after_extent += (end - rva) if end else size
                for x in reasons_v1:
                    lifted_by[x] += 1
            for x in left:
                remaining[x] += 1
            for x in r:
                if reasons_v1 & LIFTED:
                    remaining['census:' + x] += 1
        out['sample'] = {'functions': len(rows), 'bytes_by_survey_size': bytes_total,
                         'v1_supported': before, 'v1_supported_bytes': bytes_before,
                         'v2_supported': after, 'v2_supported_bytes_by_survey_size': bytes_after,
                         'v2_supported_bytes_by_chain_extent': bytes_after_extent,
                         'lifted_reasons': dict(lifted_by.most_common()),
                         'remaining_reasons': dict(remaining.most_common())}
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
