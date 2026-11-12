"""Build private per-function context packs and Drafter task directories.

Usage (repository root; see tools/ghidra/README.md):

    python3 tools/ghidra/export_pack.py packs <list file>     # packs + task dirs
    python3 tools/ghidra/export_pack.py refresh .local/packs/<build id>/<rva> ...  # aids only, no Ghidra
    python3 tools/ghidra/export_pack.py refresh --tasks .local/tasks/<id> ...     # + class material, BRIEF
    python3 tools/ghidra/export_pack.py plan --extend Actor --label batch3        # propose class units
    python3 tools/ghidra/export_pack.py survey --sample 2000 --seed 1
    python3 tools/ghidra/export_pack.py bind --task .local/tasks/<id> [--object <candidate.obj>]  # attempt does this itself

The list file has one function per line: `<build id> <rva> <task id> [<unit .cpp path>]`.
Machine-specific paths (Ghidra, project, image, community checkouts) come from a private config,
by default .local/config/export_pack.json. Everything this tool writes is game-derived and goes
under .local/ only; the tool itself contains no game data.
"""
import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE))
from pecoff import (EH_HANDLERS, EH_LAYOUTS, FUNCINFO_MAGIC, TYPE_DESCRIPTOR_NAME, UNW_FLAG_CHAININFO,  # noqa: E402
                    UNW_FLAG_EHANDLER, UNW_FLAG_UHANDLER, CoffObject, PeImage, Reject, eh_size, unwind_header)
import community_ids  # noqa: E402

PACK_SCHEMA = 1
TASK_SCHEMA = 1
DEFAULT_CONFIG = REPO / '.local/config/export_pack.json'
DEFAULT_RECIPE = 'msvc-19.16.27054-o2'
# Placeholder until bind reads the decorated name from a compiled object. The attempt command
# needs a non-empty symbol to run at all; the comparator then fails this function with a
# boundary reason, and the fetched object is what bind reads.
UNBOUND = 'unbound:'
REGS = ['RAX', 'RCX', 'RDX', 'RBX', 'RSP', 'RBP', 'RSI', 'RDI'] + ['R%d' % i for i in range(8, 16)]
UWOP = {0: 'PUSH_NONVOL', 1: 'ALLOC_LARGE', 2: 'ALLOC_SMALL', 3: 'SET_FPREG', 4: 'SAVE_NONVOL',
        5: 'SAVE_NONVOL_FAR', 6: 'EPILOG', 7: 'SPARE', 8: 'SAVE_XMM128', 9: 'SAVE_XMM128_FAR',
        10: 'PUSH_MACHFRAME'}
# Reasons that make comparator contract v2 refuse the function outright (or that leave the
# exporter unable to give the map what the comparator needs). Handlers, chained entries, several
# .pdata entries and switch tables are compared by v2 and are no longer reasons by themselves.
UNSUPPORTED = {'unwind-version', 'unsupported-unwind', 'unsupported-eh-handler', 'eh-handler-unidentified',
               'eh-funcinfo-unsupported', 'eh-funclet-without-pdata', 'eh-code-outside-function-and-funclets',
               'eh-data-unreadable', 'multiple-pdata', 'pdata-not-at-entry', 'addr64', 'jump-table',
               'import-thunk', 'thunk', 'unresolvable-reference', 'split-body', 'not-a-function'}


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------------------------------------
# Image facts the comparator also sees: .pdata, unwind info, DIR64 base relocations, imports.

class ImageFacts:
    def __init__(self, path):
        self.blob = Path(path).read_bytes()
        self.sha256 = sha256_bytes(self.blob)
        self.pe = PeImage(self.blob)
        pdata = sorted(self.pe.runtime_functions())
        self.pdata_begins = [b for b, _, _ in pdata]
        self.pdata = pdata
        self.pdata_at = {b: (e, u) for b, e, u in pdata}
        lfanew = struct.unpack_from('<I', self.blob, 60)[0]
        opt = lfanew + 24
        self.dirs = [struct.unpack_from('<II', self.blob, opt + 112 + 8 * i) for i in range(16)]
        (self.size_of_image,) = struct.unpack_from('<I', self.blob, opt + 56)
        self.dir64 = self._dir64()
        self.imports = self._imports()

    def read(self, rva, size):
        return self.pe.read(rva, size, 'read')[1]

    def section(self, rva):
        try:
            return self.pe.section_for(rva)
        except Exception:
            return None

    def _dir64(self):
        rva, size = self.dirs[5]
        out = []
        if not size:
            return out
        blob = self.read(rva, size)
        pos = 0
        while pos + 8 <= size:
            page, block = struct.unpack_from('<II', blob, pos)
            if block < 8:
                break
            for i in range(8, block, 2):
                (entry,) = struct.unpack_from('<H', blob, pos + i)
                if entry >> 12 == 10:
                    out.append(page + (entry & 0xFFF))
            pos += block
        out.sort()
        return out

    def _cstr(self, rva):
        sec = self.section(rva)
        start = sec.raw_ptr + rva - sec.vaddr
        end = self.blob.index(b'\0', start)
        return self.blob[start:end].decode('ascii', 'replace')

    def _imports(self):
        rva, size = self.dirs[1]
        out = {}
        if not size:
            return out
        pos = rva
        while True:
            oft, _, _, name_rva, ft = struct.unpack('<IIIII', self.read(pos, 20))
            if not ft:
                break
            dll = self._cstr(name_rva)
            lookup = oft or ft
            i = 0
            while True:
                (entry,) = struct.unpack('<Q', self.read(lookup + 8 * i, 8))
                if not entry:
                    break
                fn = ('#%d' % (entry & 0xFFFF)) if entry >> 63 else self._cstr((entry & 0x7FFFFFFF) + 2)
                out[ft + 8 * i] = (dll, fn)
                i += 1
            pos += 20
        return out

    def pdata_intersecting(self, start, end):
        i = bisect.bisect_right(self.pdata_begins, start) - 1
        out = []
        i = max(i, 0)
        while i < len(self.pdata) and self.pdata[i][0] < end:
            b, e, u = self.pdata[i]
            if e > start:
                out.append((b, e, u))
            i += 1
        return out

    def dir64_in(self, start, end):
        # An 8-byte field that starts up to 7 bytes before the range still patches bytes inside it.
        lo = bisect.bisect_left(self.dir64, start - 7)
        hi = bisect.bisect_left(self.dir64, end)
        return self.dir64[lo:hi]

    def unwind(self, unwind_rva):
        head = self.read(unwind_rva, 4)
        vf, prolog, count, frame = head
        version, flags = vf & 7, vf >> 3
        codes = self.read(unwind_rva + 4, 2 * count) if count else b''
        ops, i = [], 0
        while i < count:
            off, b = codes[2 * i], codes[2 * i + 1]
            op, info = b & 0xF, b >> 4
            extra = 0
            text = UWOP.get(op, 'OP%d' % op)
            if op == 0:
                text += ' ' + REGS[info]
            elif op == 1:
                extra = 1 if info == 0 else 2
                text += ' size=%s' % ('slot' if extra == 1 else 'far')
            elif op == 2:
                text += ' 0x%x' % (info * 8 + 8)
            elif op == 3:
                text += ' %s+0x%x' % (REGS[frame & 0xF], (frame >> 4) * 16)
            elif op in (4, 8):
                extra = 1
                reg = REGS[info] if op == 4 else 'XMM%d' % info
                scale = 8 if op == 4 else 16
                if i + 1 < count:
                    text += ' %s [rsp+0x%x]' % (reg, struct.unpack_from('<H', codes, 2 * (i + 1))[0] * scale)
            elif op in (5, 9):
                extra = 2
                text += ' ' + (REGS[info] if op == 5 else 'XMM%d' % info)
            ops.append('@%d %s' % (off, text))
            i += 1 + extra
        return {'version': version, 'flags': flags, 'prolog_size': prolog, 'code_slots': count,
                'frame_register': REGS[frame & 0xF] if frame & 0xF else None, 'codes': ops}


def unwind_form(u):
    if u is None:
        return 'none (leaf without .pdata)'
    flag_names = [n for bit, n in ((1, 'EHANDLER'), (2, 'UHANDLER'), (4, 'CHAININFO')) if u['flags'] & bit]
    return 'v%d flags=%s prolog=%d slots=%d%s: %s' % (
        u['version'], '|'.join(flag_names) or '0', u['prolog_size'], u['code_slots'],
        (' frame=' + u['frame_register']) if u['frame_register'] else '', '; '.join(u['codes']) or 'no codes')


# ---------------------------------------------------------------------------------------------
# Target-side reading of what comparator contract v2 compares: chained unwind entries, switch
# tables after the code, and exception handler data. The unwind header rules and the handler
# data layouts are the comparator's own (tools/pecoff.py: unwind_header, EH_HANDLERS, EH_LAYOUTS),
# so this walk reads the image with the same definitions instead of a second copy of them. It
# reads only the target; whether a candidate matches is still the comparator's decision.

EXEC = 0x20000000


def chain_root(img, begin, unwind_rva, depth=0):
    """The begin RVA of the entry an unwind chain ends at (the entry itself when not chained)."""
    try:
        flags, length = unwind_header(img.read(unwind_rva, 4), 'unwind info')
    except Reject:
        return begin
    if not flags & UNW_FLAG_CHAININFO or depth > 32:
        return begin
    parent, _, parent_unwind = struct.unpack('<III', img.read(unwind_rva + length, 12))
    return chain_root(img, parent, parent_unwind, depth + 1)


def chained_parts(img, rva):
    """Every .pdata entry other than `rva`'s own whose unwind chain ends at `rva`, in address order."""
    if getattr(img, '_chained', None) is None:
        img._chained = {}
        for b, e, u in img.pdata:
            root = chain_root(img, b, u)
            if root != b:
                img._chained.setdefault(root, []).append((b, e, u))
    return sorted(img._chained.get(rva, []))


def is_padding(blob):
    return all(b == 0xCC for b in blob)


def function_extent(img, rva, end):
    """(end, chained entries, split): the range grows over chained entries that follow it with
    only int3 padding between; a chained entry elsewhere means a split function (unsupported)."""
    parts, split = chained_parts(img, rva), False
    for b, e, _ in parts:
        between = [x for x in img.pdata_begins[bisect.bisect_right(img.pdata_begins, end - 1):]
                   if x < b] if b > end else []
        if b == end or (b > end and not between and is_padding(img.read(end, b - end))):
            end = e
        else:
            split = True
    return end, parts, split


def next_boundary(img, end):
    """The next .pdata begin at or after `end`, bounding how far a switch table can reach."""
    i = bisect.bisect_left(img.pdata_begins, end)
    return img.pdata_begins[i] if i < len(img.pdata_begins) else end + 0x10000


def switch_tables(img, rva, code_end, referenced):
    """End of the switch tables MSVC places after the code in the function's section, or code_end.

    A dword table is a run of two or more image-relative entries into [rva, code_end), starting at
    the next 4-byte boundary after int3 padding. A byte index table follows it when the function
    references the byte after the dword table (`referenced`: data targets the analysis saw); its
    length is not encoded anywhere, so it runs to int3 padding or the next .pdata entry.
    """
    limit = next_boundary(img, code_end)
    start = (code_end + 3) & ~3
    if start + 8 > limit or not is_padding(img.read(code_end, start - code_end)):
        return code_end, 0
    pos, entries = start, 0
    while pos + 4 <= limit and rva <= struct.unpack('<I', img.read(pos, 4))[0] < code_end:
        pos += 4
        entries += 1
    if entries < 2:
        return code_end, 0
    if pos in referenced:
        while pos < limit and img.read(pos, 1)[0] < entries:
            pos += 1
    return pos, entries


def handler_name(img, handler_rva, addrlib, communities):
    """Name of a language-specific handler: an import thunk's import, a configured name, or a
    community name for its Address Library id; None when nothing names it."""
    try:
        head = img.read(handler_rva, 6)
    except Exception:
        return None
    if head[:2] == b'\xff\x25':
        slot = handler_rva + 6 + struct.unpack('<i', head[2:])[0]
        if slot in img.imports:
            return img.imports[slot][1]
    named = getattr(img, 'handler_names', {}).get(handler_rva)
    if named:
        return named
    for c in communities:
        for n in c.names(addrlib['by_rva'].get(handler_rva, [])):
            if n['name'].split('::')[-1] in EH_HANDLERS:
                return n['name'].split('::')[-1]
    return None


def type_descriptor_symbol(img, td_rva):
    """The object-file symbol of a TypeDescriptor: `??_R0` + its decorated name without the dot + `@8`."""
    name = img.pe.read(td_rva + TYPE_DESCRIPTOR_NAME, 256, 'type descriptor')[1].split(b'\0', 1)[0]
    text = name.decode('ascii', 'replace')
    return '??_R0' + text[1:] + '@8' if text.startswith('.') else None


def eh_facts(img, addrlib, communities, rva, entries):
    """Handlers, caught types and funclets the comparator will need for this function's entries.

    Walks every unwind entry (the function's, then each funclet's) the way the comparator binds
    them: handler RVA after the codes, handler data by EH_HANDLERS/EH_LAYOUTS, code fields outside
    the function's range are funclets with their own .pdata entries. Returns reasons for anything
    contract v2 refuses or this walk cannot name.
    """
    reasons, handlers, types, funclets, inner = [], {}, {}, {}, []
    seen_structs, queue, done = set(), list(entries), set()
    lo, hi = entries[0][0], entries[-1][1]

    def code(target):
        if not target or lo <= target < hi or target in funclets:
            return
        entry = img.pdata_at.get(target)
        if entry is None:
            # An IP-to-state boundary inside a funclet; checked once every funclet is known.
            inner.append(target)
            return
        funclets[target] = entry[0] - target
        queue.append((target, entry[0], entry[1]))

    def walk(kind, at, count=1):
        size = eh_size(kind)
        for i in range(count):
            base = at + i * size
            if (kind, base) in seen_structs:
                continue
            seen_structs.add((kind, base))
            values = {}
            for n, fdef in enumerate(EH_LAYOUTS[kind]):
                name, how = fdef[0], fdef[1]
                value = struct.unpack('<I', img.read(base + 4 * n, 4))[0]
                values[name] = value
                if how == 'code':
                    code(value)
                elif how == 'type' and value:
                    types[value] = type_descriptor_symbol(img, value)
                elif how == 'code_or_int':
                    sec = img.section(value) if value else None
                    if sec is not None and sec.flags & EXEC:
                        code(value)
                elif how == 'array' and value:
                    walk(fdef[2], value, values[fdef[3]] if fdef[3] else 1)
            if kind == 'funcinfo' and values['magic'] != FUNCINFO_MAGIC:
                reasons.append('eh-funcinfo-unsupported')

    while queue:
        begin, end, unwind_rva = queue.pop(0)
        if begin in done:
            continue
        done.add(begin)
        try:
            flags, length = unwind_header(img.read(unwind_rva, 4), 'unwind info')
        except Reject as exc:
            reasons.append(exc.reason)
            continue
        if not flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
            continue
        h_rva = struct.unpack('<I', img.read(unwind_rva + length, 4))[0]
        name = handler_name(img, h_rva, addrlib, communities)
        if name is None:
            reasons.append('eh-handler-unidentified')
            continue
        if name not in EH_HANDLERS:
            reasons.append('unsupported-eh-handler')
            continue
        handlers[name] = h_rva
        data = unwind_rva + length + 4
        for layout in EH_HANDLERS[name]:
            if layout == 'funcinfo':
                walk('funcinfo', struct.unpack('<I', img.read(data, 4))[0])
                data += 4
            elif layout == 'scope_table':
                count = struct.unpack('<I', img.read(data, 4))[0]
                walk('scope_entry', data + 4, count)
                data += 4 + count * eh_size('scope_entry')
    for t in sorted(set(inner)):
        if any(n and f <= t < f + n for f, n in funclets.items()):
            continue
        sec = img.section(t)
        if sec is None or not sec.flags & EXEC:
            reasons.append('eh-code-outside-function-and-funclets')
        elif not any(f <= t < f + n for f, n in funclets.items() if n):
            # A leaf funclet (an unwind action that only adjusts and jumps) has no .pdata entry,
            # so its length is known only from the candidate's section, which the comparator binds.
            funclets[t] = None
    return {'handlers': handlers, 'caught_types': types, 'funclets': funclets, 'reasons': sorted(set(reasons))}


# ---------------------------------------------------------------------------------------------
# Address Library (format 5, used by 1.7.x) and community names.

def read_addrlib_v5(path):
    buf = Path(path).read_bytes()
    fmt, a, b, c, d = struct.unpack_from('<5i', buf, 0)
    if fmt != 5:
        raise SystemExit(f'{path}: Address Library format {fmt}; only format 5 is read here')
    (count,) = struct.unpack_from('<I', buf, 0x5C)
    if len(buf) != 0x60 + 4 * count:
        raise SystemExit(f'{path}: size does not match its id count')
    offs = struct.unpack_from('<%dI' % count, buf, 0x60)
    by_rva = {}
    for i, o in enumerate(offs):
        if o:
            by_rva.setdefault(o, []).append(i)
    return {'version': '%d.%d.%d.%d' % (a, b, c, d), 'sha256': sha256_bytes(buf), 'by_rva': by_rva}


class Community:
    """Names and headers from one CommonLibSSE checkout, with its licence label."""

    def __init__(self, label, root, revision, licence, cache_dir):
        self.label, self.root, self.revision, self.licence = label, Path(root), revision, licence
        cache = Path(cache_dir) / f'ids-{label}-{revision[:12]}.json'
        if cache.is_file():
            rows = json.loads(cache.read_text())
        else:
            rows = community_ids.scan(str(self.root))
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(rows))
        self.by_ae = {}
        for ae, se, kind, name, how, src in rows:
            self.by_ae.setdefault(ae, []).append({'name': name, 'kind': kind, 'how': how, 'source': src,
                                                  'se_id': se})
        self._class_index = None

    def describe(self):
        return f'{self.label} {self.revision} ({self.licence})'

    def names(self, ae_ids):
        out = []
        for ae in ae_ids:
            for row in self.by_ae.get(ae, []):
                out.append(dict(row, ae_id=ae, origin=self.describe()))
        # Declared identifiers are stronger evidence than the enclosing-definition heuristic.
        out.sort(key=lambda r: (r['how'] != 'table', r['kind'] in ('unknown',)))
        return out

    def class_index(self):
        if self._class_index is None:
            idx = {}
            pat = re.compile(r'^\s*(?:class|struct)\s+(?:alignas\([^)]*\)\s+)?(?:\w+_API\s+)?(\w+)\b(?!\s*;)')
            for p in sorted((self.root / 'include').rglob('*.h')):
                try:
                    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
                except OSError:
                    continue
                for n, line in enumerate(lines):
                    m = pat.match(line)
                    if m and not line.rstrip().endswith(';'):
                        idx.setdefault(m.group(1), []).append((p, n))
            self._class_index = idx
        return self._class_index

    def class_excerpt(self, cls, limit=400):
        hits = self.class_index().get(cls, [])
        # Prefer the header named after the class, where CommonLibSSE keeps the definition.
        hits.sort(key=lambda h: h[0].stem != cls)
        for path, start in hits:
            lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
            depth, opened = 0, False
            for n in range(start, min(len(lines), start + 2000)):
                code = lines[n].split('//', 1)[0]
                depth += code.count('{') - code.count('}')
                opened = opened or '{' in code
                if opened and depth <= 0:
                    body = lines[max(0, start - 2):n + 1]
                    truncated = len(body) > limit
                    return {'path': str(path.relative_to(self.root)), 'line': start + 1,
                            'text': '\n'.join(body[:limit]) + ('\n// ... truncated' if truncated else ''),
                            'origin': self.describe()}
        return None

    def source_excerpt(self, source, before=12, after=12):
        path, _, line = source.rpartition(':')
        p = self.root / path
        if not p.is_file():
            return None
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        n = int(line) - 1
        return {'path': path, 'line': n + 1, 'origin': self.describe(),
                'text': '\n'.join(lines[max(0, n - before):n + after + 1])}


def reference_declarations(refs, comms):
    """Declaration lines of referenced members, so a Drafter can declare callees and globals
    without opening the community headers. Lines come from the owning class body only."""
    out, seen = [], set()
    for r in refs:
        for cn in r.get('community_names', [])[:1]:
            cls, member = owning_class(cn['name']), short_name(cn['name']).split('::')[-1]
            if (cls, member) in seen:
                continue
            seen.add((cls, member))
            found = False
            for c in comms if cls else []:
                ex = c.class_excerpt(cls)
                if not ex:
                    continue
                hits = [ln.strip() for ln in ex['text'].splitlines()
                        if re.search(r'\b' + re.escape(member) + r'\s*[\(;\[{=]', ln)]
                if hits:
                    out.append(f'// 0x{r["target_rva"]:x} {cls}::{member} -- {c.describe()} {ex["path"]}')
                    out.extend(hits[:4])
                    found = True
                    break
            if not found:
                # Free functions and namespace members: show the community wrapper around the id.
                origin = next((c for c in comms if c.describe() == cn['origin']), None)
                ex = origin.source_excerpt(cn['source'], before=8, after=2) if origin else None
                if ex:
                    out.append(f'// 0x{r["target_rva"]:x} {short_name(cn["name"])} -- {ex["origin"]} '
                               f'{ex["path"]}:{ex["line"]} (wrapper around the id; {cn["how"]})')
                    out.extend(ex['text'].splitlines())
    return out


def owning_class(name):
    parts = [p for p in re.split(r'::|\.', name) if p]
    while parts and parts[0] in ('RE', 'Offset', 'NG_b93280e'):
        parts.pop(0)
    return parts[-2] if len(parts) >= 2 else None


def short_name(name):
    parts = [p for p in name.split('::') if p]
    while parts and parts[0] in ('RE', 'Offset'):
        parts.pop(0)
    return '::'.join(parts)


# ---------------------------------------------------------------------------------------------
# Ghidra run.

def run_ghidra(cfg, selector, out_dir, mode, log):
    env = dict(os.environ, JAVA_HOME=cfg['java_home'], GHIDRA_HEADLESS_MAXMEM=cfg.get('maxmem', '8G'))
    cmd = [cfg['analyze_headless'], cfg['project_dir'], cfg['project_name'], '-process', cfg['program'],
           '-noanalysis', '-readOnly', '-scriptPath', str(HERE), '-postScript', 'ExportPack.java',
           selector, str(out_dir), mode]
    t0 = time.monotonic()
    with open(log, 'w') as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT, env=env)
    if rc != 0 or not (Path(out_dir) / 'meta.tsv').is_file():
        raise SystemExit(f'Ghidra failed (exit {rc}); see {log}')
    return time.monotonic() - t0


def load_meta(out_dir):
    meta = {}
    with open(Path(out_dir) / 'meta.tsv') as fh:
        for line in fh:
            rva, found, name, nsyms, ranges, ninstr, computed, ctargets, thunk, fp, cond, icalls = \
                line.rstrip('\n').split('\t')
            meta[int(rva, 16)] = {
                'found': found == '1', 'ghidra_name': name,
                'ranges': [] if ranges == '-' else [tuple(int(x, 16) for x in r.split('-')) for r in ranges.split(',')],
                'n_instr': int(ninstr), 'computed_jumps': int(computed), 'computed_targets': int(ctargets),
                'thunk': thunk == '1', 'fp_arith': int(fp), 'cond_branches': int(cond),
                'indirect_calls': int(icalls)}
    return meta


def iter_refs(out_dir):
    """(function rva, [reference]) groups in file order; ExportPack writes one function's rows together,
    so a whole-image run never needs every reference in memory at once."""
    cur, group = None, []
    with open(Path(out_dir) / 'refs.tsv') as fh:
        for line in fh:
            rva, off, rtype, target, mnem, opi, names, tentry = line.rstrip('\n').split('\t')
            rva = int(rva, 16)
            if rva != cur:
                if cur is not None:
                    yield cur, group
                cur, group = rva, []
            group.append({'offset': int(off), 'ref_type': rtype, 'target': int(target, 16), 'mnemonic': mnem,
                          'operand': int(opi), 'ghidra_names': names, 'target_entry': int(tentry)})
    if cur is not None:
        yield cur, group


def load_ghidra(out_dir):
    refs = {}
    for rva, group in iter_refs(out_dir):
        refs.setdefault(rva, []).extend(group)
    return load_meta(out_dir), refs


# ---------------------------------------------------------------------------------------------
# Suitability for comparator contract v2.

def constant_symbol(img, target, mnemonic):
    # MSVC names scalar and vector literals by content (__real@ / __xmm@); the operand width
    # follows from the SSE mnemonic, and conversions read their source width.
    m = mnemonic.upper()
    if 'SS2' in m:
        width = 4
    elif 'SD2' in m:
        width = 8
    elif m.endswith(('PS', 'PD')) or m.startswith(('MOVDQ', 'PAND', 'PXOR', 'POR', 'PSHUF')):
        width = 16
    elif m.endswith('SS'):
        width = 4
    elif m.endswith('SD'):
        width = 8
    else:
        return None
    try:
        data = img.read(target, width)
    except Exception:
        return None
    if width == 16:
        return '__xmm@' + data[::-1].hex()
    return '__real@' + data[::-1].hex()


def classify(img, addrlib, communities, rva, gmeta, grefs):
    """Return the pack facts for one function: range, unwind, exception data, references and a
    verdict against comparator contract v2."""
    reasons, cautions = [], []
    if not gmeta or not gmeta['found']:
        return {'rva': rva, 'verdict': 'unsupported', 'reasons': ['not-a-function'], 'cautions': []}
    entry = img.pdata_at.get(rva)
    ranges = gmeta['ranges']
    body_lo = min(r[0] for r in ranges)
    body_hi = max(r[1] for r in ranges)
    own, eh, tables = [], None, 0
    if entry:
        end, unwind_rva = entry
        # Chained entries continue the same function (contract v2 compares them); its size runs
        # to the last one, as the candidate's section does.
        end, parts, split = function_extent(img, rva, end)
        if split:
            reasons.append('split-body')
        own = [(rva, entry[0], unwind_rva)] + parts
        size = end - rva
        unwind = img.unwind(unwind_rva)
    else:
        size = body_hi - rva
        unwind = None
        if img.pdata_intersecting(rva, rva + size):
            reasons.append('pdata-not-at-entry')
        else:
            cautions.append('no-pdata: leaf; size taken from the analysis body, not from .pdata')
            # Without .pdata the end is only as good as the analysis; MSVC pads to the next
            # 16-byte boundary with int3, so anything else after the body casts doubt on it.
            pad = (-(rva + size)) % 16
            try:
                tail = img.read(rva + size, pad) if pad else b''
            except Exception:
                tail = b'?'
            if tail.strip(b'\xcc'):
                cautions.append('code, not int3 padding, follows the analysis body: an unaligned compiler '
                                'thunk (adjustor, EH helper) or a wrong size')
    # A switch's tables follow the code inside the function's section, so they belong to its size.
    table_end, tables = switch_tables(img, rva, rva + size, {r['target'] for r in grefs})
    size = table_end - rva
    if own:
        try:
            eh = eh_facts(img, addrlib, communities, rva, own)
        except (Reject, struct.error, ValueError) as exc:
            eh = {'handlers': {}, 'caught_types': {}, 'funclets': {}, 'reasons': ['eh-data-unreadable']}
            cautions.append(f'exception data could not be read: {exc}')
        reasons += eh['reasons']
    funclets = sorted((eh or {}).get('funclets', {}).items())

    def inside(t):
        return rva <= t < rva + size or any(f <= t < f + (n or 1) for f, n in funclets)

    if len(ranges) > 1 and not all(inside(a) and inside(b - 1) for a, b in ranges if b > a):
        reasons.append('split-body')
    hi = max(rva + size, body_hi)
    lo = min(rva, body_lo)
    entries = img.pdata_intersecting(lo, hi)
    known = {b for b, _, _ in own} | {f for f, _ in funclets}
    if any(b not in known for b, _, _ in entries):
        reasons.append('multiple-pdata')
    if body_hi > rva + size and entry and not inside(body_hi - 1):
        cautions.append('analysis body extends %d bytes past the .pdata end' % (body_hi - rva - size))
    for b, e, u in entries:
        if b in known and img.unwind(u)['version'] != 1:
            reasons.append('unwind-version')
    if img.dir64_in(rva, rva + size):
        reasons.append('addr64')
    if gmeta['computed_targets'] >= 2 and not tables:
        # Recovered switch targets but no table after the code: a layout contract v2 does not compare.
        reasons.append('jump-table')
    elif gmeta['computed_jumps'] and not tables:
        cautions.append('indirect jump without recovered targets (tail call through a register or memory, '
                        'or an unrecovered switch)')
    if funclets:
        cautions.append('funclet code references are not listed (the analysis covered the parent only); '
                        'bind them by hint or by position')
    if gmeta['thunk']:
        reasons.append('thunk')
    refs, seen = [], set()
    for r in grefs:
        t = r['target']
        if inside(t):
            continue
        if r['target_entry'] == rva and r['ref_type'] not in ('DATA', 'READ', 'WRITE', 'READ_WRITE'):
            # A branch into this function's own code past the primary .pdata range: no relocation,
            # and the range problem itself is already reported (multiple-pdata, split-body).
            continue
        key = (r['offset'], t)
        if key in seen:
            continue
        seen.add(key)
        rt = r['ref_type']
        kind = ('call' if 'CALL' in rt else 'jump' if 'JUMP' in rt else
                'write' if rt == 'WRITE' else 'read' if 'READ' in rt else 'address')
        sec = img.section(t)
        ref = {'from_offset': r['offset'], 'kind': kind, 'ghidra_ref_type': rt, 'mnemonic': r['mnemonic'],
               'target_rva': t, 'section': sec.name if sec else None, 'ae_ids': addrlib['by_rva'].get(t, []),
               'ghidra_names': r['ghidra_names'], 'symbol': None}
        execsec = bool(sec and sec.flags & 0x20000000)
        if t == 0:
            # `lea reg, [__ImageBase]`: MSVC's base for image-relative tables such as switch tables.
            ref.update(resolution='image-base', symbol='__ImageBase')
        elif sec is None and not 0 < t < img.size_of_image:
            # Segment-relative operands (gs:[0x58] for TLS) look like addresses to the analysis but
            # carry no relocation, so they place no requirement on the symbol map.
            continue
        elif t in img.imports:
            dll, fn = img.imports[t]
            ref.update(resolution='import', symbol='__imp_' + fn, import_name=f'{dll}!{fn}')
            if size <= 8 and gmeta['computed_jumps']:
                reasons.append('import-thunk')
        elif sec is None:
            ref['resolution'] = 'outside-image'
            reasons.append('unresolvable-reference')
        elif execsec and r['target_entry'] == -1 and t not in img.pdata_at:
            ref['resolution'] = 'code-no-function'
            cautions.append('code address 0x%x lies in no analysed function (unwind-less leaf or lambda?)' % t)
        elif execsec and r['target_entry'] != t and t not in img.pdata_at:
            ref['resolution'] = 'mid-function'
            reasons.append('unresolvable-reference')
        elif sec.name == '.rdata' and constant_symbol(img, t, r['mnemonic']):
            # A literal the compiler emits itself: the object names it by content, whatever id the
            # Address Library also gives the image's copy.
            ref.update(resolution='constant', symbol=constant_symbol(img, t, r['mnemonic']))
        elif ref['ae_ids']:
            ref['resolution'] = 'addrlib-id'
        elif execsec:
            ref['resolution'] = 'function-no-id'
            cautions.append('call/jump target 0x%x has no Address Library id' % t)
        else:
            if r['ghidra_names'].split(' | ')[0].startswith(('s_', 'u_')):
                ref['resolution'] = 'string-literal'
                cautions.append('string literal at 0x%x: map needs its ??_C@ decorated name' % t)
            else:
                ref['resolution'] = 'data-no-id'
                cautions.append('data target 0x%x has no Address Library id' % t)
        names = []
        for c in communities:
            names.extend(c.names(ref['ae_ids']))
        ref['community_names'] = [{'name': n['name'], 'kind': n['kind'], 'how': n['how'], 'source': n['source'],
                                   'origin': n['origin'], 'ae_id': n['ae_id']} for n in names[:4]]
        refs.append(ref)
    # The comparator resolves the handler and each caught type through the symbol map like any
    # external reference, so they are listed as references and reach the task's symbols.json.
    for name, h_rva in sorted((eh or {}).get('handlers', {}).items()):
        refs.append({'from_offset': None, 'kind': 'eh-handler', 'ghidra_ref_type': None, 'mnemonic': None,
                     'target_rva': h_rva, 'section': None, 'ae_ids': addrlib['by_rva'].get(h_rva, []),
                     'ghidra_names': '', 'symbol': name, 'resolution': 'eh-handler', 'community_names': []})
    for td_rva, symbol in sorted((eh or {}).get('caught_types', {}).items()):
        if symbol is None:
            cautions.append('caught type at 0x%x has no readable decorated name' % td_rva)
        refs.append({'from_offset': None, 'kind': 'eh-type', 'ghidra_ref_type': None, 'mnemonic': None,
                     'target_rva': td_rva, 'section': None, 'ae_ids': addrlib['by_rva'].get(td_rva, []),
                     'ghidra_names': '', 'symbol': symbol, 'resolution': 'eh-type', 'community_names': []})
    reasons = sorted(set(reasons))
    verdict = 'unsupported' if reasons else ('caution' if cautions else 'supported')
    counts = {}
    for ref in refs:
        counts[ref['kind']] = counts.get(ref['kind'], 0) + 1
    return {'rva': rva, 'size': size, 'verdict': verdict, 'reasons': reasons, 'cautions': sorted(set(cautions)),
            'pdata_entries': len(entries), 'unwind': unwind, 'unwind_form': unwind_form(unwind),
            'dir64_in_range': len(img.dir64_in(rva, rva + size)), 'ghidra': gmeta, 'references': refs,
            'reference_counts': counts, 'chained_entries': len(own) - 1 if own else 0, 'switch_table_entries': tables,
            'eh': {'handlers': {k: hex(v) for k, v in (eh or {}).get('handlers', {}).items()},
                   'caught_types': len((eh or {}).get('caught_types', {})),
                   'funclets': [{'rva': hex(f), 'size': n} for f, n in funclets]}}


# ---------------------------------------------------------------------------------------------
# Drafter aids: virtual tables, observed field offsets, trimmed types, calling convention.

def image_base(img):
    lfanew = struct.unpack_from('<I', img.blob, 60)[0]
    return struct.unpack_from('<Q', img.blob, lfanew + 24 + 24)[0]


def vtable_index(comms):
    """{class name: AE id of its primary vtable} from the community VTABLE_<Class>[0] ids."""
    out = {}
    for c in comms:
        for ae, rows in c.by_ae.items():
            for r in rows:
                m = re.fullmatch(r'(?:RE::)?VTABLE_(?:__)?([A-Za-z_]\w*)\[0\]', r['name'])
                if r['kind'] == 'vtable' and m:
                    out.setdefault(m.group(1), ae)
    return out


def rtti_bases(img, vtable_rva):
    """Class names of the RTTI hierarchy behind a vtable, most derived first, or []."""
    try:
        base = image_base(img)
        (col_va,) = struct.unpack('<Q', img.read(vtable_rva - 8, 8))
        sig, _, _, _, chd, _ = struct.unpack('<6I', img.read(col_va - base, 24))
        if sig != 1:
            return []
        _, _, count, bca = struct.unpack('<4I', img.read(chd, 16))
        names = []
        for i in range(min(count, 32)):
            (bcd,) = struct.unpack('<I', img.read(bca + 4 * i, 4))
            (td,) = struct.unpack('<I', img.read(bcd, 4))
            raw = img.read(td + 16, 256).split(b'\0', 1)[0].decode('ascii', 'replace')
            m = re.fullmatch(r'\.\?A[VU](.+)@@', raw)
            # Nested classes are spelled Outer__Inner in NG's VTABLE_ ids; anonymous namespaces are dropped.
            parts = [x for x in m.group(1).split('@') if x and not x.startswith('?')] if m else [raw]
            names.append('__'.join(reversed(parts)))
        return names
    except Exception:  # a reading aid: a malformed or absent RTTI chain just yields no table
        return []


def vtable_slots(img, addrlib, comms, vtable_rva, limit=400):
    """[(slot, rva, community name)] until the first entry that is not a code address."""
    base, out = image_base(img), []
    for i in range(limit):
        try:
            (va,) = struct.unpack('<Q', img.read(vtable_rva + 8 * i, 8))
        except Exception:
            break
        rva = va - base
        sec = img.section(rva) if 0 < rva < img.size_of_image else None
        if not sec or not sec.flags & 0x20000000:
            break
        names = []
        for c in comms:
            names += [short_name(n['name']) for n in c.names(addrlib['by_rva'].get(rva, []))
                      if n['kind'] not in ('vtable', 'rtti', 'nirtti')]
        out.append((i, rva, names[0] if names else None))
    return out


def declared_slots(comms, cls):
    """{slot: virtual declaration} from the community header's `// NN` slot comments for one class."""
    for c in comms:
        if 'GPL' in c.licence:
            continue
        ex = c.class_excerpt(cls, limit=2000)
        if not ex:
            continue
        out, depth = {}, 0
        for line in ex['text'].splitlines():
            code, _, comment = line.partition('//')
            # Only the class's own body: nested types declare their own slots.
            if depth == 1 and 'virtual' in code:
                m = re.match(r'\s*([0-9A-Fa-f]{2,3})\b', comment)
                if m:
                    out[int(m.group(1), 16)] = ' '.join(code.split())
            depth += code.count('{') - code.count('}')
        return out
    return {}


def vtable_text(img, addrlib, comms, cls):
    """Slot tables of the owning class and its RTTI bases, as text for the pack."""
    index = vtable_index(comms)
    if cls not in index:
        return None
    by_id = {i: rva for rva, ids in addrlib['by_rva'].items() for i in ids}
    own = by_id.get(index[cls])
    if own is None:
        return None
    lines = ['// Virtual tables from the pinned image: slot, byte offset, target RVA, Address Library name,',
             '// and the virtual that the community header declares for that slot (its `// NN` comment).',
             f'// Classes: {cls} and its RTTI bases; a slot first appears in the most basic class listing it.']
    for name in rtti_bases(img, own) or [cls]:
        rva = by_id.get(index.get(name)) if name in index else None
        if rva is None:
            lines.append(f'\n// {name}: no community vtable id')
            continue
        slots = vtable_slots(img, addrlib, comms, rva)
        declared = declared_slots(comms, name.split('__')[-1])
        lines.append(f'\n// {name}: vtable at 0x{rva:x}, {len(slots)} slots')
        for i, target, cname in slots:
            lines.append(f'  {i:3d}  +0x{8 * i:03x}  0x{target:x}  {cname or "-"}'
                         + (f'  | {declared[i]}' if i in declared else ''))
    return '\n'.join(lines) + '\n'


MEM_OPERAND = re.compile(r'(byte|word|dword|qword|xmmword) ptr \[([A-Z0-9]+)(?: \+ (0x[0-9a-f]+))?\]')


def observed_offsets(listing):
    """[(displacement, base register, width, instruction offset)] of non-stack memory operands."""
    out = []
    for line in listing.splitlines():
        m = re.match(r'\s*\+0x([0-9a-f]+)\s+(.*)', line)
        if not m:
            continue
        for width, reg, disp in MEM_OPERAND.findall(m.group(2).split('[CALL')[0]):
            if reg in ('RSP', 'RBP', 'RIP') or reg.startswith('0X'):
                continue
            out.append((int(disp, 16) if disp else 0, reg, width, int(m.group(1), 16)))
    return out


def trim_excerpt(text, offsets, keep_names, full_limit=4000, context=1):
    """The class excerpt cut to its declaration head, virtuals, named members and touched offsets."""
    if len(text) <= full_limit:
        return text, False
    lines = text.splitlines()
    keep = set(range(0, min(len(lines), 25)))
    for n, line in enumerate(lines):
        code, _, comment = line.partition('//')
        m = re.search(r'\b([0-9A-Fa-f]{2,4})\b', comment)
        hit = m and int(m.group(1), 16) in offsets and not code.strip().startswith(('virtual', 'public', 'private'))
        if 'virtual' in code or re.match(r'\s*(public|private|protected):', code) or hit \
                or any(re.search(r'\b' + re.escape(k) + r'\b', code) for k in keep_names):
            keep.update(range(max(0, n - context), min(len(lines), n + context + 1)) if hit else {n})
    out, skipped = [], 0
    for n, line in enumerate(lines):
        if n in keep:
            if skipped:
                out.append(f'\t// ... {skipped} lines omitted')
                skipped = 0
            out.append(line)
        else:
            skipped += 1
    if skipped:
        out.append(f'\t// ... {skipped} lines omitted')
    return '\n'.join(out), True


TYPE_WORD = re.compile(r'\b([A-Z][A-Za-z0-9_]+)\b')
FLOAT_TYPES = {'float', 'double'}


def declaration_of(excerpt_text, method):
    for line in (excerpt_text or '').splitlines():
        code = line.split('//', 1)[0]
        if re.search(r'\b' + re.escape(method) + r'\s*\(', code):
            return code.strip()
    return None


def convention_notes(decl, owning_class):
    """Calling and return convention facts for MSVC x64 from a community declaration line."""
    if not decl:
        return ['- No declaration found in the community excerpt; derive the signature from the listing.']
    static = bool(re.search(r'\bstatic\b', decl)) or not owning_class
    head, _, rest = decl.partition('(')
    params = [p.strip() for p in rest.rsplit(')', 1)[0].split(',') if p.strip() and p.strip() != 'void']
    ret = re.sub(r'\b(static|virtual|inline|constexpr|explicit|\[\[nodiscard\]\])\b', '', head).strip()
    ret = ' '.join(ret.split()[:-1])
    notes = [f'- Community declaration: `{decl}`.']
    regs_i, regs_f = ['RCX', 'RDX', 'R8', 'R9'], ['XMM0', 'XMM1', 'XMM2', 'XMM3']
    slot = 0
    if not static:
        notes.append('- Member function: `this` arrives in RCX.')
        slot = 1
    hidden = bool(ret) and ret not in ('void', 'bool') and '*' not in ret and '&' not in ret \
        and TYPE_WORD.search(ret) and not re.fullmatch(r'(const\s+)?(std::)?u?int\d+_t|float|double|char|int|unsigned.*', ret)
    if hidden:
        reg = 'RDX' if not static else 'RCX'
        notes.append(f'- Returns `{ret}` by value. MSVC x64 returns a class in RAX only if it is 1, 2, 4 or 8 bytes '
                     'and has no user-declared constructor, destructor or copy assignment, no base class, no '
                     'virtuals and no private or protected data; otherwise the caller passes the result address in '
                     f'{reg} and the function returns it in RAX. If the listing copies {reg} to RAX before `RET`, the '
                     'type is returned through that hidden pointer: give it a user-declared constructor (or copy '
                     'constructor) and build the result in one named local.')
        slot += 1
    for i, p in enumerate(params):
        pos = slot + i
        if pos >= 4:
            notes.append(f'- Parameter {i + 1} `{p}` is passed on the stack.')
            continue
        is_float = p.split()[0] in FLOAT_TYPES and '*' not in p and '&' not in p
        notes.append(f'- Parameter {i + 1} `{p}` arrives in {(regs_f if is_float else regs_i)[pos]}.')
    if ret in FLOAT_TYPES:
        notes.append('- Returns a float in XMM0.')
    return notes


LISTING_ROW = re.compile(r'\s*\+0x([0-9a-f]+)\s+(\S+)')
FP_COMPARE = {'UCOMISS', 'UCOMISD', 'COMISS', 'COMISD'}
EQUALITY_USE = {'JZ', 'JNZ', 'JE', 'JNE', 'SETZ', 'SETNZ', 'SETE', 'SETNE', 'CMOVZ', 'CMOVNZ', 'CMOVE', 'CMOVNE'}
PARITY_USE = {'JP', 'JNP', 'JPE', 'JPO', 'SETP', 'SETNP', 'SETPE', 'SETPO', 'CMOVP', 'CMOVNP'}


def fp_equality_without_parity(listing):
    """Offsets of SSE compares whose flags feed an equality test with no parity test nearby.

    Under /fp:precise MSVC guards a float ==/!= with a parity test (an unordered compare sets
    ZF and PF), so an equality use of ZF right after (u)comis with no parity use in the next few
    instructions points to /fp:fast. Ordered tests (ja/jb...) need no parity check either way.
    """
    rows = [(int(m.group(1), 16), m.group(2).upper()) for m in map(LISTING_ROW.match, listing.splitlines()) if m]
    out = []
    for i, (off, mnem) in enumerate(rows):
        if mnem not in FP_COMPARE:
            continue
        window = [mn for _, mn in rows[i + 1:i + 5]]
        # Flags survive only until the next instruction that writes them; stop the window there.
        for k, mn in enumerate(window):
            if mn in FP_COMPARE or mn in ('TEST', 'CMP', 'ADD', 'SUB', 'AND', 'OR', 'XOR', 'INC', 'DEC'):
                window = window[:k]
                break
        if any(mn in EQUALITY_USE for mn in window) and not any(mn in PARITY_USE for mn in window):
            out.append(off)
    return out


FP_SENSITIVE = re.compile(r'^(?:(?:ADD|SUB|MUL|DIV|SQRT|MIN|MAX|CMP|RCP|RSQRT)(?:SS|SD|PS|PD)|U?COMIS[SD]|CVT\w+)$')


def fp_sensitive(listing):
    """True when the listing computes, compares or converts floats, where /fp:fast and /fp:precise can
    differ. Moves, loads, stores and XORPS zeroing are emitted the same under both."""
    return any(FP_SENSITIVE.match(m.group(2).upper()) for m in map(LISTING_ROW.match, listing.splitlines()) if m)


def drafter_aids(pack_dir, img, addrlib, comms, ident, listing_text, excerpt, build_id=None):
    """Write vtables.txt, signature-types.h and the convention/offset notes; returns README lines and files."""
    files, lines = {}, []
    cls = ident.get('owning_class') if ident else None
    method = short_name(ident['community_name']).split('::')[-1] if ident and ident.get('community_name') else None
    if cls:
        vt = vtable_text(img, addrlib, comms, cls)
        if vt:
            (pack_dir / 'vtables.txt').write_text(vt)
            files['vtables'] = 'vtables.txt'
    offsets = observed_offsets(listing_text or '')
    lines += ['', '## Observed memory operands (non-stack)', '']
    if offsets:
        lines.append('| displacement | base register | width | at |')
        lines.append('|---|---|---|---|')
        for disp, reg, width, at in offsets[:40]:
            lines.append(f'| 0x{disp:x} | {reg} | {width} | +0x{at:x} |')
        lines.append('')
        lines.append('Registers are as at that instruction; at entry RCX is `this` for a member function. Match '
                     'these displacements to the member offsets in the class excerpt.')
    else:
        lines.append('None.')
    decl = declaration_of(excerpt['text'] if excerpt else '', method) if method else None
    lines += ['', '## Calling and return convention', ''] + convention_notes(decl, cls)
    if decl:
        wanted = sorted({w for w in TYPE_WORD.findall(decl) if w not in (cls, method)})
        parts = []
        for name in wanted[:6]:
            for c in comms:
                if 'GPL' in c.licence:
                    continue
                ex = c.class_excerpt(name, limit=120)
                if ex:
                    body, _ = trim_excerpt(ex['text'], {d for d, *_ in offsets}, [], full_limit=1500)
                    parts.append(f'// {ex["origin"]}: {ex["path"]}:{ex["line"]}\n{body}\n')
                    break
        if parts:
            (pack_dir / 'signature-types.h').write_text('\n'.join(parts))
            files['signature_types'] = 'signature-types.h'
    fp_eq = fp_equality_without_parity(listing_text or '')
    if fp_eq:
        lines += ['', '**Float equality without a parity branch** at ' + ', '.join(f'+0x{o:x}' for o in fp_eq)
                  + ': `/fp:precise` (the default recipe) emits `jp` there, `/fp:fast` does not. The function',
                  'likely needs the `o2-fpfast` recipe; its task says which recipe it uses.']
    lines += ['', 'Virtual slots: `' + files.get('vtables', 'none (no community vtable id)') + '`; types in the '
              'signature: `' + files.get('signature_types', 'none') + '`.', '']
    if cls and build_id:
        class_dir = REPO / '.local/packs' / build_id / 'class' / cls
        if (class_dir / 'README.md').is_file():
            lines += [f'Class material shared by every function of `{cls}` in this batch (vtables, offsets '
                      f'observed across all of them, declarations): `{class_dir.relative_to(REPO)}/README.md`.', '']
    return files, lines


# ---------------------------------------------------------------------------------------------
# Aids from the whole-image tables of build_function_table.py (optional: absent tables just mean
# the sections are left out): call-site census (P5), EH object lifetimes (P6), class skeletons.

ANALYSIS = REPO / '.local/analysis'
_analysis = {}


def analysis_tables(root=None):
    """(functions by rva, call-site census by callee rva, classes by name, table meta) or None."""
    root = Path(root or ANALYSIS)
    key = str(root)
    if key not in _analysis:
        if not (root / 'functions.jsonl').is_file():
            _analysis[key] = None
        else:
            fns = {}
            with open(root / 'functions.jsonl') as fh:
                for line in fh:
                    r = json.loads(line)
                    fns[r['rva']] = r
            census = json.loads((root / 'callsites.json').read_text()) if (root / 'callsites.json').is_file() else {}
            classes = {}
            if (root / 'classes.jsonl').is_file():
                with open(root / 'classes.jsonl') as fh:
                    for line in fh:
                        c = json.loads(line)
                        classes[c['class']] = c
            meta = json.loads((root / 'table-meta.json').read_text()) if (root / 'table-meta.json').is_file() else {}
            _analysis[key] = (fns, {int(k): v for k, v in census.items()}, classes, meta)
    return _analysis[key]


def best_name(row):
    """One display name for a table row: checked slot names first, then id names that do not
    contradict the image's vftables, with the source tag."""
    if not row:
        return None
    order = {'ng-slot': 0, 'ng-id': 1, 'po3-slot': 2, 'po3-id': 3, 'meh321': 4}
    names = [n for n in row.get('names', []) if n.get('agrees_with_vtable') is not False and n['how'] != 'placeholder']
    names.sort(key=lambda n: order.get(n['source'], 9))
    return f'{names[0]["name"]} [{names[0]["source"]}]' if names else None


def census_summary(c):
    """`N sites; arity a:n ...; slot widths; result` from one census entry."""
    if not c:
        return None
    arity = ', '.join(f'{k}:{v}' for k, v in sorted(c['arity'].items(), key=lambda kv: int(kv[0])))
    slots = []
    for k, widths in sorted(c['slots'].items(), key=lambda kv: int(kv[0])):
        top = sorted(widths.items(), key=lambda kv: -kv[1])
        slots.append(f'{k}=' + '/'.join(f'{w}x{n}' for w, n in top[:3]))
    res = ', '.join(f'{k} {v}' for k, v in sorted(c['result'].items(), key=lambda kv: -kv[1]))
    return f'{c["sites"]} sites from {c["callers"]} callers; highest argument slot set + 1: {arity}; ' \
           f'slots set: {" ".join(slots) or "none"}; result: {res}'


def signature_evidence(rva, refs, root=None):
    """README lines and pack.json data for P5: what callers of this function and of its callees
    set up before the call."""
    t = analysis_tables(root)
    if not t:
        return [], None
    fns, census, _, _ = t
    own = census.get(rva)
    lines = ['', '## Observed signature evidence (call-site census)', '',
             'Per direct call site, the argument registers (RCX/RDX/R8/R9 or XMM0-3 by position) and stack slots',
             '(`[rsp+0x20+8k]`, slot 4+k) written since the last branch or call, and how RAX/XMM0 is used after',
             'the call. Widths: i1..i8 integer bytes, p8 an address (lea), f4/f8 float/double, x16 vector. A value',
             'passed through unchanged is not seen, so counts are lower bounds. Evidence, not a declaration.', '',
             f'- This function as a callee: {census_summary(own) or "no direct call sites"}.']
    data = {'self': own, 'callees': {}}
    seen = set()
    rows = []
    for r in refs or []:
        if r.get('kind') != 'call' or r['target_rva'] in seen:
            continue
        seen.add(r['target_rva'])
        c = census.get(r['target_rva'])
        if not c:
            continue
        data['callees'][hex(r['target_rva'])] = c
        rows.append(f'| 0x{r["target_rva"]:x} | {best_name(fns.get(r["target_rva"])) or "-"} | {census_summary(c)} |')
    if rows:
        lines += ['', '| callee | name [source] | census over all its call sites in the image |', '|---|---|---|'] + rows
    return lines, data


def lifetime_outline(img, rva, root=None):
    """README lines and data for P6: the unwind-map states of a C++ EH function, the destructor
    each state's funclet calls, and the code offsets that run in each state."""
    entry = img.pdata_at.get(rva)
    if not entry:
        return [], None
    import build_function_table as bft
    try:
        flags, length = unwind_header(img.read(entry[1], 4), 'unwind info')
        if not flags & (UNW_FLAG_EHANDLER | UNW_FLAG_UHANDLER):
            return [], None
        (h_rva,) = struct.unpack('<I', img.read(entry[1] + length, 4))
        name = handler_name(img, h_rva, {'by_rva': {}}, [])
        o = bft.eh_outline(img, rva, entry[1], name or getattr(img, 'handler_names', {}).get(h_rva))
    except (Reject, struct.error, ValueError):
        return [], None
    if not o or not o.get('states'):
        return [], None
    t = analysis_tables(root)
    fns = t[0] if t else {}
    ranges = {}
    ips = sorted(o['ip_to_state'])
    for i, (ip, st) in enumerate(ips):
        end = ips[i + 1][0] if i + 1 < len(ips) else None
        ranges.setdefault(st, []).append((ip - rva, (end - rva) if end else None))
    lines = ['', '## Object lifetimes (C++ EH unwind map)', '',
             f'{len(o["states"])} states, {len(o["try_blocks"])} try blocks. A state is entered after an object with a '
             'destructor (or a `new` awaiting its constructor) is complete; its funclet destroys it on unwind, then',
             'unwinding continues at `to`. Offsets are from the function start; a funclet outside the parent says',
             'which destructor (and so which type) the state owns. Declare one destructible local or temporary per state.',
             '', '| state | to | funclet | destructor it calls | code offsets in this state |', '|---|---|---|---|---|']
    data = []
    for s in o['states']:
        fn = fns.get(s['action']) if s['action'] else None
        calls = []
        for callee in (fn or {}).get('callees', []) + (fn or {}).get('tail_callees', []):
            calls.append(f'0x{callee:x} {best_name(fns.get(callee)) or ""}'.strip())
        offs = ', '.join(f'+0x{a:x}..' + (f'+0x{b:x}' if b is not None and b >= 0 else 'end')
                         for a, b in ranges.get(s['state'], []) if a >= 0)
        lines.append(f'| {s["state"]} | {s["to_state"]} | {hex(s["action"]) if s["action"] else "-"} | '
                     f'{"; ".join(calls) or "-"} | {offs or "-"} |')
        data.append({'state': s['state'], 'to_state': s['to_state'], 'funclet': s['action'], 'calls': calls,
                     'offsets': ranges.get(s['state'], [])})
    for i, tb in enumerate(o['try_blocks']):
        lines.append(f'\nTry block {i}: states {tb["try_low"]}..{tb["try_high"]}, catch up to {tb["catch_high"]}, '
                     f'{len(tb["catches"])} handler(s).')
    return lines, {'states': data, 'try_blocks': o['try_blocks']}


def class_skeleton_text(cls, comms, root=None):
    t = analysis_tables(root)
    if not t or not t[2]:
        return None
    import class_skeleton
    cfg = {'ng_revision': comms[0].revision, 'po3_revision': comms[1].revision if len(comms) > 1 else None,
           'meh321_revision': (t[3].get('inputs') or {}).get('meh321_names') or '0' * 12}
    try:
        return class_skeleton.render(t[2], cls, cfg, t[3].get('build_id') or 'sse-steam-1-7-104')
    except SystemExit:
        return None


# ---------------------------------------------------------------------------------------------
# Packs and tasks.

def load_config(path):
    cfg = json.loads(Path(path).read_text())
    for key in ('analyze_headless', 'java_home', 'project_dir', 'project_name', 'program', 'image',
                'addrlib', 'ng_root', 'ng_revision'):
        if not cfg.get(key):
            raise SystemExit(f'config {path}: missing {key}')
    return cfg


def setup(cfg):
    target = json.loads((REPO / 'builds/target.json').read_text())
    img = ImageFacts(cfg['image'])
    # Statically linked handlers have no import to name them; the private config may.
    img.handler_names = {int(k, 16): v for k, v in (cfg.get('eh_handler_names') or {}).items()}
    if img.sha256 != target['image_sha256']:
        raise SystemExit('image SHA-256 differs from builds/target.json; packs are only built for the pinned image')
    addrlib = read_addrlib_v5(cfg['addrlib'])
    cache = REPO / '.local/packs/_cache'
    comms = [Community('CommonLibSSE-NG', cfg['ng_root'], cfg['ng_revision'], 'MIT', cache)]
    if cfg.get('po3_root'):
        comms.append(Community('powerof3/CommonLibSSE', cfg['po3_root'], cfg['po3_revision'],
                               'GPL-3.0, local use only', cache))
    return target, img, addrlib, comms


def community_identity(comms, ae_ids):
    for c in comms:
        rows = [r for r in c.names(ae_ids) if r['kind'] not in ('vtable', 'rtti', 'nirtti')]
        if rows:
            return rows[0], c
    return None, None


def write_pack(pack_dir, fact, target, addrlib, comms, gdir, timing, img):
    pack_dir.mkdir(parents=True, exist_ok=True)
    rva = fact['rva']
    ae_ids = addrlib['by_rva'].get(rva, [])
    ident, comm = community_identity(comms, ae_ids)
    if ident is None:
        ident = table_identity(rva)
    excerpt = source = None
    if ident:
        cls = owning_class(ident['name'])
        if cls:
            # NG first: its MIT licence lets type and field names be published with attribution.
            for c in comms:
                excerpt = c.class_excerpt(cls)
                if excerpt:
                    break
        source = comm.source_excerpt(ident['source']) if comm else None
        if source and excerpt and source['path'] == excerpt['path'] and comm.describe() == excerpt['origin'] \
                and excerpt['line'] <= source['line'] <= excerpt['line'] + excerpt['text'].count('\n'):
            source = None
    gpl = bool(excerpt and 'GPL' in excerpt['origin'])
    decls = reference_declarations(fact.get('references', []), comms)
    if decls:
        name = 'reference-decls.GPL-local-only.h' if any('GPL' in d for d in decls) else 'reference-decls.h'
        (pack_dir / name).write_text('\n'.join(decls) + '\n')
    files = {}
    src = Path(gdir) / ('%x' % rva)
    for name in ('listing.txt', 'decompiled.c'):
        if (src / name).is_file():
            shutil.copyfile(src / name, pack_dir / name)
            files[name] = name
    if decls:
        files['reference_decls'] = name
    listing = (pack_dir / 'listing.txt').read_text() if (pack_dir / 'listing.txt').is_file() else ''
    if excerpt:
        name = 'class-excerpt.GPL-local-only.h' if gpl else 'class-excerpt.h'
        method = short_name(ident['name']).split('::')[-1]
        text, trimmed = trim_excerpt(excerpt['text'], {d for d, *_ in observed_offsets(listing)}, [method])
        (pack_dir / name).write_text(f'// {excerpt["origin"]}: {excerpt["path"]}:{excerpt["line"]}'
                                     + (' (trimmed to the declaration head, virtuals, this method and the members at '
                                        'observed offsets)' if trimmed else '') + '\n' + text + '\n')
        files['class_excerpt'] = name
    if source:
        name = 'source-excerpt.GPL-local-only.cpp' if 'GPL' in source['origin'] else 'source-excerpt.cpp'
        (pack_dir / name).write_text(f'// {source["origin"]}: {source["path"]}:{source["line"]}\n'
                                     + source['text'] + '\n')
        files['source_excerpt'] = name
    pack = {
        'pack_schema': PACK_SCHEMA, 'private': 'game-derived; never copy into tracked files or uploads',
        'build_id': target['build_id'], 'image_sha256': target['image_sha256'],
        'rva': rva, 'rva_hex': hex(rva), 'size': fact.get('size'),
        'identity': {
            'ae_ids': ae_ids, 'address_library': f'{addrlib["version"]} sha256 {addrlib["sha256"]}',
            'community_name': short_name(ident['name']) if ident else None,
            'community_kind': ident['kind'] if ident else None,
            'name_how': ident['how'] if ident else None,
            'name_source': f'{ident["origin"]} {ident["source"]}' if ident else None,
            'name_origin': 'COMMUNITY' if ident else 'GUESS',
            'owning_class': owning_class(ident['name']) if ident else None,
            'ghidra_name': fact.get('ghidra', {}).get('ghidra_name')},
        'pdata_entries': fact.get('pdata_entries'), 'unwind': fact.get('unwind'),
        'unwind_form': fact.get('unwind_form'), 'dir64_in_range': fact.get('dir64_in_range'),
        'chained_entries': fact.get('chained_entries'), 'switch_table_entries': fact.get('switch_table_entries'),
        'eh': fact.get('eh'),
        'verdict': fact['verdict'], 'reasons': fact['reasons'], 'cautions': fact['cautions'],
        'reference_counts': fact.get('reference_counts', {}), 'references': fact.get('references', []),
        'instructions': fact.get('ghidra', {}).get('n_instr'),
        'indirect_calls': fact.get('ghidra', {}).get('indirect_calls'),
        'fp_arith': fact.get('ghidra', {}).get('fp_arith'),
        'cond_branches': fact.get('ghidra', {}).get('cond_branches'),
        'files': files, 'timing_seconds': timing,
        'fp_equality_without_parity': fp_equality_without_parity(listing)}
    aid_files, aid_lines = drafter_aids(pack_dir, img, addrlib, comms, pack['identity'], listing, excerpt,
                                       target['build_id'])
    files.update(aid_files)
    aid_lines += table_aids(pack, img)
    (pack_dir / 'pack.json').write_text(json.dumps(pack, indent=2, default=hex) + '\n')
    (pack_dir / 'README.md').write_text(render_pack_readme(pack) + '\n'.join(aid_lines))
    return pack


def table_identity(rva, root=None):
    """A community-style identity from the function table when no NG/po3 id names the function:
    a checked vftable slot name or a meh321 id name, with the owner the image's vftables give."""
    t = analysis_tables(root)
    row = t[0].get(rva) if t else None
    if not row:
        return None
    order = {'ng-slot': 0, 'po3-slot': 1, 'meh321': 2}
    names = sorted((n for n in row.get('names', []) if n['source'] in order and n['how'] != 'placeholder'
                    and n.get('agrees_with_vtable') is not False), key=lambda n: order[n['source']])
    if not names:
        return None
    n = names[0]
    origin = {'ng-slot': 'CommonLibSSE-NG (MIT) slot comment', 'po3-slot': 'powerof3/CommonLibSSE (GPL-3.0) slot comment',
              'meh321': 'meh321 Address Library names (permission)'}[n['source']]
    owner = (row.get('owner') or {}).get('class')
    name = n['name']
    if owner and n['source'].endswith('-slot'):
        name = owner.split('::')[-1] + '::' + name.split('::')[-1]
    return {'name': name, 'kind': 'func', 'how': n['how'], 'source': f'function table ({n["source"]})',
            'origin': origin, 'se_id': None, 'table_source': n['source']}


def table_aids(pack, img):
    """P5 and P6 sections for one pack, and the sibling-source pointers; also stored in pack.json."""
    sig_lines, sig = signature_evidence(pack['rva'], pack.get('references', []))
    life_lines, life = lifetime_outline(img, pack['rva'])
    pack['observed_signature'] = sig
    pack['object_lifetimes'] = life
    sib_lines = sibling_lines((pack.get('identity') or {}).get('owning_class'), [pack['rva']])
    return sig_lines + life_lines + sib_lines + ([''] if sig_lines or life_lines or sib_lines else [])


# ---------------------------------------------------------------------------------------------
# Sibling source: pointers into the FNV decompilation (maintainer decision, docs/authorizations.md)
# from the private index of tools/build_fnv_index.py. Only paths, lines and signature lines go into
# a pack; the Drafter opens the file itself, so a pack does not carry whole sibling bodies.

FNV_INDEX = 'fnv_index.jsonl'
SIBLING_REPO = 'momusdigital/fnv_decomp'
ACCESSOR_BYTES = 48
_sibling = {}


def sibling_index(root=None):
    """{'by_rva', 'by_class', 'revision'} from <analysis>/fnv_index.jsonl, or None when it is absent."""
    root = Path(root or ANALYSIS)
    key = str(root)
    if key not in _sibling:
        path = root / FNV_INDEX
        if not path.is_file():
            _sibling[key] = None
        else:
            by_rva, by_class = {}, {}
            with open(path) as fh:
                for line in fh:
                    r = json.loads(line)
                    if r.get('class'):
                        by_class.setdefault(r['class'], []).append(r)
                    for o in r.get('ours', []):
                        # A positional join whose names disagree is more likely a shifted vtable than
                        # a renamed method (about a quarter of named slot pairs agree), so it is dropped.
                        if o['how'] == 'slot' and o.get('same_name') is False:
                            continue
                        by_rva.setdefault(o['rva'], []).append((r, o))
            meta = path.with_suffix('.meta.json')
            rev = json.loads(meta.read_text()).get('revision') if meta.is_file() else None
            _sibling[key] = {'by_rva': by_rva, 'by_class': by_class, 'revision': rev}
    return _sibling[key]


def _sibling_ref(r):
    where = f'{r["source"]}:{r["line"]}' if r.get('line') else f'{r["source"]} (no line found)'
    opt = r.get('opt') or 'flags unknown'
    sig = f': `{r["signature"]}`' if r.get('signature') else ''
    return f'`{where}` ({opt}, {r["size"]} bytes){sig}'


def sibling_lines(cls, rvas, root=None, limit=12):
    """README lines naming the FNV file and line of each function's same-named (or same-slot)
    method and of the class's small named methods; [] without an index or any match."""
    index = sibling_index(root)
    if not index:
        return []
    out, listed = [], set()
    for rva in rvas:
        for r, o in index['by_rva'].get(rva, []):
            if r['symbol'] in listed:
                continue  # joined both by name and by slot: one line is enough
            how = 'same name' if o['how'] == 'name' else f'same slot {o["slot"]} (positional guess; our slot is unnamed)'
            out.append(f'- `0x{rva:x}`: `{r["class"]}::{r["method"]}` {_sibling_ref(r)}; {how}.')
            listed.add(r['symbol'])
    small = sorted((r for r in index['by_class'].get(cls or '', []) if not r.get('placeholder') and r.get('line')
                    and r['size'] <= ACCESSOR_BYTES and r['symbol'] not in listed),
                   key=lambda r: (r['method'], r['address']))
    accessors = []
    for r in small:
        if not accessors or accessors[-1]['method'] != r['method']:
            accessors.append(r)
    if not out and not accessors:
        return []
    rev = (index.get('revision') or '')[:8] or 'unknown revision'
    lines = ['', f'## Sibling source ({SIBLING_REPO}@{rev}, private clone `.local/sources/fnv_decomp`)', '',
             'Caution: Fallout: New Vegas 1.4.0.525 is a 32-bit build of an older engine version, and most of its '
             'game units are unoptimised (`/Od`); read it for shape and names, never for offsets, layouts or slots. '
             f'Label what you take `SIBLING({SIBLING_REPO}@{rev}, no-licence)`; a reused body also needs a '
             '`Sibling source:` header line.', '']
    lines += out or ['- No same-named method for the functions here.']
    if accessors:
        lines += ['', f'Small named methods of `{cls}` there (at most {ACCESSOR_BYTES} bytes; accessors and helpers):']
        lines += [f'- `{r["method"]}` {_sibling_ref(r)}' for r in accessors[:limit]]
        if len(accessors) > limit:
            lines.append(f'- and {len(accessors) - limit} more (`.local/analysis/{FNV_INDEX}`, class `{cls}`).')
    return lines


def render_pack_readme(p):
    ident = p['identity']
    lines = [f'# PRIVATE context pack: {p["build_id"]} {p["rva_hex"]}', '',
             'Game-derived (listing, decompiler output, community excerpts). Local use only; never copy any',
             'part into a tracked file, issue, PR, log or upload.', '',
             f'- Size: {p["size"]} bytes (from .pdata, through {p.get("chained_entries") or 0} chained entries and '
             f'{p.get("switch_table_entries") or 0} switch-table entries, unless a caution says otherwise); '
             f'{p["instructions"]} instructions; {p["cond_branches"]} conditional branches; '
             f'{p["indirect_calls"]} indirect calls (register or vtable unless listed below); {p["fp_arith"]} SSE arithmetic instructions.',
             f'- Community name: `{ident["community_name"]}` ({ident["name_origin"]}, unverified; '
             f'{ident["name_how"]}; {ident["name_source"]}).',
             f'- Address Library ids: {ident["ae_ids"] or "none"}. Ghidra label: `{ident["ghidra_name"]}`.',
             f'- Owning class: `{ident["owning_class"]}`; excerpt: `{p["files"].get("class_excerpt", "none")}`; '
             f'name use site: `{p["files"].get("source_excerpt", "none")}`.',
             f'- Unwind: {p["unwind_form"]}; .pdata entries touching the range: {p["pdata_entries"]}; '
             f'DIR64 relocations in range: {p["dir64_in_range"]}.',
             f'- Exception data: handlers {", ".join(f"`{k}` at {v}" for k, v in ((p.get("eh") or {}).get("handlers") or {}).items()) or "none"}; '
             f'{(p.get("eh") or {}).get("caught_types", 0)} caught types; '
             f'{len((p.get("eh") or {}).get("funclets") or [])} funclets (compared apart from the size).',
             f'- Comparator v2 verdict: **{p["verdict"]}**' + (f' ({", ".join(p["reasons"])})' if p['reasons'] else '')
             + '.']
    for c in p['cautions']:
        lines.append(f'- Caution: {c}.')
    lines += ['', '## References leaving the function', '',
              '| +off | kind | target | section | resolution | AE ids | community name | map symbol |',
              '|---|---|---|---|---|---|---|---|']
    for r in p['references']:
        cn = r['community_names'][0] if r['community_names'] else None
        cname = f'`{short_name(cn["name"])}` ({cn["how"]}, {cn["origin"].split(" ")[0]} {cn["source"]})' if cn else \
            f'Ghidra `{r["ghidra_names"]}`'
        offset = 'EH data' if r['from_offset'] is None else f'0x{r["from_offset"]:x}'
        lines.append(f'| {offset} | {r["kind"]} {r["mnemonic"] or ""} | 0x{r["target_rva"]:x} | '
                     f'{r["section"]} | {r["resolution"]} | {r["ae_ids"] or "-"} | {cname} | '
                     f'`{r["symbol"] or "Drafter declares"}` |')
    if not p['references']:
        lines.append('| - | none | | | | | | |')
    unnamed = [r for r in p['references'] if not r['community_names'] and not r['symbol']]
    if unnamed:
        lines += ['', 'Targets without a community name (' + ', '.join(f'0x{r["target_rva"]:x}' for r in unnamed)
                  + '): any name you give them is a GUESS; bind them by hand to the RVA above and say so in the',
                  'source header. Declarations of the named references: `' + p['files'].get('reference_decls', 'none') + '`.']
    elif p['references']:
        lines += ['', 'Declarations of the named references: `' + p['files'].get('reference_decls', 'none') + '`.']
    lines += ['', 'Files: `listing.txt` (Ghidra 12.2 instruction listing with references), `decompiled.c`,',
              '`pack.json` (all of the above, machine-readable).', '']
    return '\n'.join(lines)


def shared_unit_functions(unit_cpp):
    """Inventory entries whose match record already binds this unit: editing it re-opens them."""
    out = []
    progress = json.loads((REPO / 'data/progress.json').read_text())
    for fn in progress['functions']:
        rec = fn.get('report')
        if rec and (REPO / rec).is_file() and unit_cpp in (REPO / rec).read_text():
            runs = json.loads((REPO / rec).read_text()).get('runs') or [{}]
            symbol = runs[0].get('report', {}).get('function', {}).get('symbol')
            out.append({'function_id': fn['id'], 'status': fn['status'], 'record': rec, 'rva': hex(fn['rva']),
                        'size': fn['size'], 'symbol': symbol, 'community_name': fn['name']})
    return out


AREA_PREFIXES = (('Ni', 'netimmerse'), ('BS', 'bsengine'), ('TES', 'forms'), ('BGS', 'forms'))
ACTOR_CLASSES = {'Actor', 'Character', 'PlayerCharacter'}


def area_for(cls):
    """The area by prefix rule 2 of reconstruction/README.md, or None when the rule has no line for it."""
    if cls in ACTOR_CLASSES or cls.endswith('Process'):
        return 'actors'
    for prefix, area in AREA_PREFIXES:
        if cls.startswith(prefix) and cls[len(prefix):len(prefix) + 1].isupper():
            return area
    return None


def write_task(task_id, unit_cpp, recipe, packs, target, task_root, max_attempts, attempts_per_function=None):
    tdir = task_root / task_id
    tdir.mkdir(parents=True, exist_ok=True)
    old = {}
    if (tdir / 'task.json').is_file():
        # Re-exporting must not discard symbols a Drafter already bound.
        old = {f['rva']: f.get('symbol') for f in json.loads((tdir / 'task.json').read_text())['functions']}
    functions, symbols, provenance = [], {}, []
    for p in packs:
        ident = p['identity']
        functions.append({
            'rva': p['rva_hex'], 'size': p['size'],
            'symbol': old.get(p['rva_hex']) or UNBOUND + (ident['community_name'] or p['rva_hex']),
            'function_id': f'{p["build_id"]}-{p["rva_hex"]}', 'community_name': ident['community_name'],
            'name_origin': ident['name_origin'], 'verdict': p['verdict'],
            'pack': f'.local/packs/{p["build_id"]}/{p["rva_hex"]}'})
        for r in p['references']:
            if r['symbol'] and r['symbol'] not in symbols:
                symbols[r['symbol']] = {'rva': r['target_rva'], 'size': None}
                provenance.append({'name': r['symbol'], 'rva': hex(r['target_rva']), 'from': r['resolution']})
    shared = shared_unit_functions(unit_cpp)
    public_map = REPO / 'reports' / target['build_id'] / 'symbol-map.json'
    if shared and public_map.is_file():
        # The accepted functions of a shared unit resolve their references through the published
        # map; seeding the task map with it keeps the regression comparison bindable from the start.
        for k, v in json.loads(public_map.read_text())['symbols'].items():
            if k not in symbols:
                symbols[k] = v
                provenance.append({'name': k, 'rva': hex(v['rva']), 'from': public_map.relative_to(REPO).as_posix()})
    for rec in shared:
        # Compared on every attempt too, so an edit to the shared unit that breaks an accepted
        # function shows up at once instead of at integration.
        if rec['symbol'] and rec['rva'] not in {f['rva'] for f in functions}:
            functions.append({'rva': rec['rva'], 'size': rec['size'], 'symbol': rec['symbol'],
                              'function_id': rec['function_id'], 'community_name': rec['community_name'],
                              'name_origin': 'COMMUNITY', 'verdict': 'already ' + rec['status'],
                              'pack': None, 'role': 'regression'})
            symbols.setdefault(rec['symbol'], {'rva': int(rec['rva'], 16), 'size': rec['size']})
    if attempts_per_function:
        # Several functions share one budget; each needs a few compile-compare rounds of its own.
        max_attempts = attempts_per_function * sum(1 for f in functions if f.get('role') != 'regression')
    # A community `X::~X` at vtable slot 0 is a deleting destructor in the image; record which
    # destructor function the target is so binding never settles on the plain `??1`.
    sys.path.insert(0, str(REPO / 'tools' / 'verifier'))
    import bind as binding
    binding.annotate_destructors({'functions': functions}, REPO)
    classes = sorted({p['identity'].get('owning_class') or 'Unknown' for p in packs})
    task = {'task_id': task_id, 'build_id': target['build_id'], 'compiled': unit_cpp,
            'recipe': f'reconstruction/recipes/{recipe}.json', 'symbols': 'symbols.json',
            'functions': functions, 'max_attempts': max_attempts,
            'export': {'generator': 'tools/ghidra/export_pack.py', 'task_schema': TASK_SCHEMA,
                       'target_image_sha256': target['image_sha256'],
                       'unit_already_records': shared,
                       'class_material': [f'.local/packs/{target["build_id"]}/class/{c}' for c in classes],
                       'brief': f'.local/tasks/{task_id}/BRIEF.md'}}
    (tdir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
    smap_path = tdir / 'symbols.json'
    if smap_path.is_file():
        smap = json.loads(smap_path.read_text())
        for k, v in symbols.items():
            smap['symbols'].setdefault(k, v)
    else:
        smap = {'schema': 1, 'build_id': target['build_id'], 'symbols': symbols, 'folds': [],
                '_provenance': {'generator': 'tools/ghidra/export_pack.py', 'entries': provenance,
                                'note': 'bind adds task and reference symbols from the compiled object'}}
    smap_path.write_text(json.dumps(smap, indent=2) + '\n')
    (tdir / 'README.md').write_text(render_task_readme(task, packs))
    (tdir / 'BRIEF.md').write_text(render_brief(task, packs))
    return tdir


def render_task_readme(task, packs):
    lines = [f'# PRIVATE task: {task["task_id"]}', '',
             f'Build `{task["build_id"]}`. Unit `{task["compiled"]}` and the header beside it; recipe '
             f'`{task["recipe"]}`; attempt budget {task["max_attempts"]}.', '']
    shared = task['export']['unit_already_records']
    if shared:
        lines += ['**This unit already backs a match record** (' + ', '.join(
            f'`{s["function_id"]}` {s["status"]}' for s in shared) + '). Any edit to the unit changes its',
            'digest, so those records go stale and must be re-verified with the unit before integration.', '']
    lines += ['## Functions', '']
    counts = {p['rva_hex']: p['reference_counts'] for p in packs}
    for f in task['functions']:
        if f.get('role') == 'regression':
            lines.append(f'- `{f["rva"]}` {f["size"]} B `{f["community_name"]}`: already {f["verdict"][8:]}, '
                         'listed so every attempt re-checks it; keep its source behaviour unchanged.')
            continue
        lines.append(f'- `{f["rva"]}` {f["size"]} B `{f["community_name"]}` ({f["name_origin"]}), verdict '
                     f'{f["verdict"]}; pack `{f["pack"]}/README.md`; references: '
                     f'{counts.get(f["rva"]) or "none"}.')
    lines += ['', '## What must be right', '',
              '1. Each compared function must be an **external** symbol at offset 0 of its own COMDAT code',
              '   section (`/Gy` is in the recipe). The comparator finds the candidate by the exact decorated',
              '   name in `task.json` `functions[].symbol`; nothing else identifies it. That name is decided by',
              '   your declarations (class vs struct, const, virtual, parameter types, calling convention), so',
              '   the tool cannot derive it in advance. No anonymous namespaces (internal linkage is rejected).',
              '2. Every call, jump or data reference that leaves the function becomes a relocation against a',
              '   symbol you declared (or a compiler constant such as `__real@...`). The symbol map must give',
              '   each one the RVA the game encodes; a wrong or missing entry fails the comparison.',
              '3. `symbol` starts as `unbound:<community name>`. `attempt` binds names itself: after compiling',
              '   it finds each compared function in the object (by hint, by the community name, or by its',
              '   member name when that is unique, so your class or function names may differ), binds each',
              '   reference by the target\'s own encoded address when that is one of the pack\'s listed',
              '   targets, compares again in the same run, and does not count a run that could compare',
              '   nothing because of binding. It prints what it bound and what is still missing.',
              '4. When it cannot bind something (a target without a community name that the code does not',
              '   reach at the same offset, an ambiguous name), add a hint to',
              f'   `.local/tasks/{task["task_id"]}/bind-hints.json`: a JSON object mapping a decorated name',
              '   (`?...`) or a qualified name as you wrote it (`Class::member`, `FreeFunction`) to the RVA',
              '   from the pack\'s reference table, for example',
              '   `{"BSTimer::QGlobalTimeMultiplier": "0x20ccac8", "?GetArmorKind@@YAHPEAVTESObjectARMO@@@Z": "0x27edf0"}`.',
              '   A hint whose RVA is a compared function\'s RVA names that function. Never edit `symbols.json`',
              '   or `task.json` by hand, and never give an RVA the pack does not list.',
              '5. Re-run `tools/verifier/attempt .local/tasks/' + task['task_id'] + '` after every source change.',
              '   Exit 0 is review evidence only, never `matched`.', '']
    return '\n'.join(lines)


def member_offsets(excerpt_text):
    """{offset: declaration} from `// NNN` offset comments in the class's own body (not nested types)."""
    out, depth = {}, 0
    for line in (excerpt_text or '').splitlines():
        code, _, comment = line.partition('//')
        if depth == 1 and code.strip() and 'virtual' not in code and '(' not in code:
            m = re.match(r'\s*([0-9A-Fa-f]{2,4})\b', comment)
            if m:
                out.setdefault(int(m.group(1), 16), ' '.join(code.split()))
        depth += code.count('{') - code.count('}')
    return out


def class_material(cls, packs, listings, img, addrlib, comms):
    """Class-level aids from every selected function of one class: {file name: text} and facts."""
    files, facts = {}, {'class': cls, 'referenced_classes': set(), 'gpl_local_only': []}
    excerpt = None
    for c in comms:
        excerpt = c.class_excerpt(cls, limit=4000)
        if excerpt:
            break
    observed = {}
    for p in packs:
        for disp, reg, width, at in observed_offsets(listings.get(p['rva_hex'], '')):
            observed.setdefault(disp, []).append((p['rva_hex'], reg, width, at))
    methods = sorted({short_name(p['identity']['community_name']).split('::')[-1] for p in packs
                      if p['identity'].get('community_name')})
    members = member_offsets(excerpt['text']) if excerpt else {}
    if excerpt:
        text, trimmed = trim_excerpt(excerpt['text'], set(observed), methods, full_limit=6000)
        name = 'class-excerpt.GPL-local-only.h' if 'GPL' in excerpt['origin'] else 'class-excerpt.h'
        files[name] = (f'// {excerpt["origin"]}: {excerpt["path"]}:{excerpt["line"]}'
                       + (' (trimmed to the declaration head, virtuals, the selected methods and the members at '
                          'offsets observed in any selected function)' if trimmed else '') + '\n' + text + '\n')
    rows = ['| displacement | community member at that offset (own body only) | uses: function +at reg width |',
            '|---|---|---|']
    for disp in sorted(observed):
        uses = '; '.join(f'{rva} +0x{at:x} {reg} {width}' for rva, reg, width, at in observed[disp][:8])
        more = len(observed[disp]) - 8
        rows.append(f'| 0x{disp:x} | {members.get(disp, "-")} | {uses}{f"; +{more} more" if more > 0 else ""} |')
    files['offsets.md'] = '\n'.join(
        [f'# Memory operands observed across the selected {cls} functions', '',
         'Non-stack displacements from every listing of this batch\'s functions of the class. The base',
         'register is as at that instruction, so a row is `this` only where the register holds it (RCX at',
         'entry, or a copy); other rows belong to other objects. The member column matches the displacement',
         'against offset comments of the class\'s own body only: inherited members are not resolved here.', '']
        + (rows if observed else ['None observed.']) + [''])
    vt = vtable_text(img, addrlib, comms, cls)
    if vt:
        files['vtables.txt'] = vt
        own = {i: rva for rva, ids in addrlib['by_rva'].items() for i in ids}.get(vtable_index(comms).get(cls))
        bases = rtti_bases(img, own) if own is not None else []
        facts['referenced_classes'].update(b.split('__')[-1] for b in bases[1:])
    sig_types, parts = set(), []
    for p in packs:
        method = short_name(p['identity']['community_name'] or '').split('::')[-1]
        decl = declaration_of(excerpt['text'] if excerpt else '', method)
        if decl:
            sig_types.update(w for w in TYPE_WORD.findall(decl) if w not in (cls, method))
    for name in sorted(sig_types):
        for c in comms:
            if 'GPL' in c.licence:
                continue
            ex = c.class_excerpt(name, limit=120)
            if ex:
                body, _ = trim_excerpt(ex['text'], set(), [], full_limit=1500)
                parts.append(f'// {ex["origin"]}: {ex["path"]}:{ex["line"]}\n{body}\n')
                facts['referenced_classes'].add(name)
                break
    if parts:
        files['signature-types.h'] = '\n'.join(parts)
    skeleton = class_skeleton_text(cls, comms)
    if skeleton:
        files['skeleton.h'] = skeleton
    refs = [r for p in packs for r in p.get('references', [])]
    for r in refs:
        for cn in r.get('community_names', [])[:1]:
            owner = owning_class(cn['name'])
            if owner and owner != cls:
                facts['referenced_classes'].add(owner)
    decls = reference_declarations(refs, comms)
    if decls:
        name = 'reference-decls.GPL-local-only.h' if any('GPL' in d for d in decls) else 'reference-decls.h'
        files[name] = '\n'.join(decls) + '\n'
    facts['referenced_classes'].discard(cls)
    facts['methods'] = methods
    facts['gpl_local_only'] = sorted(n for n in files if 'GPL-local-only' in n)
    return files, facts


def write_class_material(task_dirs, target, img, addrlib, comms, shared_name='_shared-classes.json'):
    """Write .local/packs/<build>/class/<Class>/ for every class owning a function of the given tasks.

    One directory per class even when its functions are split over several tasks (one per recipe),
    so a Drafter taking the class reads the vtables, offsets and declarations once. Also writes
    _shared-classes.json: classes that more than one of these units uses, the candidates for a
    shared header."""
    by_class, units = {}, {}
    for t in task_dirs:
        task = json.loads((Path(t) / 'task.json').read_text())
        for f in task['functions']:
            if not f.get('pack'):
                continue
            pack = json.loads((REPO / f['pack'] / 'pack.json').read_text())
            cls = pack['identity'].get('owning_class') or 'Unknown'
            by_class.setdefault(cls, {})[pack['rva_hex']] = pack
            units.setdefault(cls, set()).add(task['compiled'])
    root = REPO / '.local/packs' / target['build_id'] / 'class'
    users = {}
    for cls, packs_by_rva in sorted(by_class.items()):
        packs = sorted(packs_by_rva.values(), key=lambda p: (p['size'] or 0, p['rva']))
        listings = {p['rva_hex']: (REPO / '.local/packs' / target['build_id'] / p['rva_hex'] / 'listing.txt')
                    .read_text() for p in packs
                    if (REPO / '.local/packs' / target['build_id'] / p['rva_hex'] / 'listing.txt').is_file()}
        files, facts = class_material(cls, packs, listings, img, addrlib, comms)
        d = root / cls
        if d.is_dir():
            for old in d.iterdir():
                old.unlink()  # a re-run must not leave a stale file from an earlier selection
        d.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (d / name).write_text(text)
        for other in facts['referenced_classes'] | {cls}:
            users.setdefault(other, set()).add(cls)
        lines = [f'# PRIVATE class material: {cls} ({target["build_id"]})', '',
                 'Game-derived. Local use only; never copy any part into a tracked file, issue, PR, log or upload.',
                 'Shared by every function of this class in the batch; the per-function packs keep the listing,',
                 'decompiler output and references of each function.', '',
                 f'Units: {", ".join(f"`{u}`" for u in sorted(units[cls]))}.', '',
                 '| RVA | size | community name | verdict | float == without parity | pack |', '|---|---|---|---|---|---|']
        for p in packs:
            fp = ', '.join(f'+0x{o:x}' for o in p.get('fp_equality_without_parity') or []) or '-'
            lines.append(f'| {p["rva_hex"]} | {p["size"]} | `{p["identity"]["community_name"]}` | {p["verdict"]} | '
                         f'{fp} | `.local/packs/{target["build_id"]}/{p["rva_hex"]}/` |')
        lines += ['', '## Files', '']
        notes = {'class-excerpt.h': 'community class body, trimmed to the head, virtuals, the selected methods and '
                                    'members at offsets observed in any selected function',
                 'offsets.md': 'displacements observed across all selected functions, with the member at each',
                 'vtables.txt': 'slot tables of the class and its RTTI bases',
                 'signature-types.h': 'trimmed declarations of the types in the selected methods\' signatures',
                 'reference-decls.h': 'declarations of everything the selected functions call or read',
                 'skeleton.h': 'header skeleton from tools/ghidra/class_skeleton.py: base chain, every virtual slot '
                               'in order with checked names or Unk_NN, verified size; start the unit header from it'}
        for name in sorted(files):
            base = name.replace('.GPL-local-only', '')
            lines.append(f'- `{name}`: {notes.get(base, "")}'
                         + (' (GPL-3.0 fallback: local naming aid only, never publish)' if 'GPL' in name else '.'))
        lines += ['', '## Calling convention per function', '']
        excerpt_text = files.get('class-excerpt.h') or files.get('class-excerpt.GPL-local-only.h') or ''
        for p in packs:
            method = short_name(p['identity']['community_name'] or '').split('::')[-1]
            lines.append(f'`{p["rva_hex"]}` {method}:')
            lines += ['  ' + n for n in convention_notes(declaration_of(excerpt_text, method), cls)]
        lines += ['', 'Other classes these functions use (declare minimal stand-ins, labelled with their source): '
                  + (', '.join(f'`{c}`' for c in sorted(facts['referenced_classes'])) or 'none') + '.', '']
        lines += sibling_lines(cls, [p['rva'] for p in packs]) + ['']
        (d / 'README.md').write_text('\n'.join(lines))
        (d / 'class.json').write_text(json.dumps({
            'class': cls, 'build_id': target['build_id'], 'units': sorted(units[cls]),
            'functions': [p['rva_hex'] for p in packs], 'files': sorted(files),
            'referenced_classes': sorted(facts['referenced_classes'])}, indent=2) + '\n')
        print(f'class {cls}: {len(packs)} functions, {", ".join(sorted(files))}')
    shared = {c: sorted(u) for c, u in sorted(users.items()) if len(u) > 1}
    root.mkdir(parents=True, exist_ok=True)
    (root / shared_name).write_text(json.dumps({
        'units': sorted(by_class), 'used_by_more_than_one_unit': shared,
        'note': 'Candidates for a shared header in their own area; moving a class there changes the digest '
                'of every unit that includes it.'}, indent=2) + '\n')
    return shared


def render_brief(task, packs):
    """At most 25 lines a Drafter brief can point to: functions smallest first, packs, risks."""
    by_rva = {p['rva_hex']: p for p in packs}
    compared = sorted((f for f in task['functions'] if f.get('role') != 'regression'),
                      key=lambda f: (f['size'] or 0, f['rva']))
    regress = [f for f in task['functions'] if f.get('role') == 'regression']
    cls = (packs[0]['identity'].get('owning_class') if packs else None) or 'Unknown'
    total = sum(f['size'] or 0 for f in compared)
    lines = [f'# Brief: {task["task_id"]}', '',
             f'Unit `{task["compiled"]}` (+ `.h`), recipe `{task["recipe"].rsplit("/", 1)[-1][:-5]}`, '
             f'budget {task["max_attempts"]} attempts for {len(compared)} functions ({total} B).',
             f'Class material first: `.local/packs/{task["build_id"]}/class/{cls}/README.md`; per-function packs '
             f'`.local/packs/{task["build_id"]}/<rva>/`.', '',
             'Order (smallest first): RVA, size, community name, references, notes']
    for i, f in enumerate(compared, 1):
        p = by_rva.get(f['rva'], {})
        notes = []
        if p.get('fp_equality_without_parity'):
            notes.append('float == without parity (fp:fast pattern)')
        notes += [c.split(':')[0] for c in p.get('cautions', [])]
        unnamed = sum(1 for r in p.get('references', []) if not r['community_names'] and not r['symbol'])
        if unnamed:
            notes.append(f'{unnamed} unnamed target(s): GUESS names + bind hint')
        if any(r['resolution'] == 'import' for r in p.get('references', [])):
            notes.append('import call')
        if f.get('destructor'):
            notes.append(f'{f["destructor"]["kind"]} ({"/".join(f["destructor"]["symbols"])}): '
                         + ('emitted only with the vftable, so define a constructor in the unit' if '??1' not in
                            f['destructor']['symbols'] else 'kind undecided, bound by size'))
        refs = ', '.join(f'{k} {v}' for k, v in sorted((p.get('reference_counts') or {}).items())) or 'none'
        lines.append(f'{i}. `{f["rva"]}` {f["size"]} B `{f["community_name"]}`; refs {refs}'
                     + (f'; {"; ".join(notes)}' if notes else ''))
    lines += ['', 'Known risks:']
    risks = []
    if regress:
        risks.append('- Shared unit: it already holds ' + ', '.join(f'`{f["community_name"]}` ({f["rva"]})'
                     for f in regress) + '; every attempt re-checks it, keep it passing and its source unchanged.')
    if task['recipe'].endswith('fpfast.json'):
        risks.append('- `/fp:fast` recipe: some functions test float equality without a parity branch; the others '
                     'do no float arithmetic, compare or conversion, so the recipe does not change them.')
    elif any(by_rva.get(f['rva'], {}).get('fp_equality_without_parity') for f in compared):
        risks.append('- A function shows the `/fp:fast` pattern under the default recipe: report it, do not '
                     'change the recipe.')
    area = task['compiled'].split('/')[1]
    if not regress and area_for(cls) != area:
        risks.append(f'- Area `{area}/` is an owning-system choice (README rule 1), not the prefix rule; '
                     'the maintainer confirms it before integration.')
    risks.append('- Class and member names are COMMUNITY (unverified); enclosing-definition names may be wrong.')
    risks.append('- Declare other classes as minimal stand-ins in your header; do not edit other units.')
    lines += risks
    extra = brief_sections(cls, packs, compared)
    return '\n'.join(lines[:25] + extra) + '\n'


# ---------------------------------------------------------------------------------------------
# Brief sections shared by unit and group briefs: existing headers to include, the cookbook rules
# the listings point to, and the FNV sibling pointers.

COOKBOOK = 'docs/matching-cookbook.md'
# One line in every unit brief (once in a group brief): the origin check runs inside `attempt`, and a
# body adapted from a community or FNV source must be declared where it is written, not afterwards.
ORIGIN_LINE = ('Body origin: `attempt` prints `origin:` lines, and `origin advice:` while an adapted community '
               'or FNV body is undeclared; declare it in the header comment of each file holding adapted code, '
               'with its licence notice (`docs/drafter-card.md`).')
COOKBOOK_RULES = {
    'flag-test': '16: a flag bit tested as load, `shr`, `test al,1` goes through a by-value bit-index '
                 'helper (`TestBit(word, n)`) from the first draft.',
    'out-param': '15: an inlined lookup that leaves the caller\'s local untouched on a miss is '
                 '`bool Find(key, T& out)` writing `out` only on a hit.',
    'small-out-param': '22: a callee\'s out-parameter placed below an 8-byte temporary in the home '
                       'slots is a small type (`bool`, `uint32_t`), not a pointer.',
    'deleting-dtor': '14, 18, 10: a slot-0 destructor is the deleting `??_G` (define a constructor so the '
                     'vftable is emitted); if it calls the plain one, declare `~X();` without a body; '
                     'a call with edx = 1 means class-scope operator new/delete.',
    'null-test': '1, 23: a null test the candidate drops means the source re-read the member; a field the '
                 'target loads after a null test is read after the test, not into a local before it.',
    'virtual-call': '11: a call through slot N needs every earlier slot declared (placeholders labelled '
                    'GUESS), inherited TESForm/NiObject slots included.',
}
_FLAG_TEST = re.compile(r'\bSHR (E?\w+),0x[0-9a-f]+\s*\n[^\n]*\b(?:TEST|AND) \w+,0x1\b', re.I)
_STACK_ARG = re.compile(r'\bLEA (?:RDX|R8|R9|RCX|EDX|R8D|R9D),\[R(?:SP|BP) [+-] [^\]]+\]', re.I)
_NULL_TEST = re.compile(r'\bTEST (R\w+),\1\b', re.I)
_VCALL = re.compile(r'\bCALL qword ptr \[R\w+ \+ 0x[0-9a-f]+\]', re.I)


def listing_traits(listing, function):
    """Cookbook-rule keys a function's listing (and its task entry) points to."""
    traits = []
    if _FLAG_TEST.search(listing):
        traits.append('flag-test')
    if _STACK_ARG.search(listing) and 'CALL' in listing.upper():
        traits += ['out-param', 'small-out-param']
    if function.get('destructor') or '~' in (function.get('community_name') or ''):
        traits.append('deleting-dtor')
    if _NULL_TEST.search(listing):
        traits.append('null-test')
    if _VCALL.search(listing):
        traits.append('virtual-call')
    return traits


def repository_headers(root=None):
    """{class: 'area/Class.h'} for every header under reconstruction/."""
    root = Path(root or REPO)
    return {p.stem: p.relative_to(root / 'reconstruction').as_posix() for p in (root / 'reconstruction').glob('*/*.h')}


def shared_headers(cls, packs, headers, classes=None):
    """(class, header) pairs a unit of `cls` may include instead of declaring a stand-in: existing
    repository headers of its RTTI ancestors and of the classes its functions reference."""
    wanted = list((classes or {}).get(cls, {}).get('ancestors') or [])
    build = packs[0]['build_id'] if packs else None
    material = REPO / '.local/packs' / (build or '-') / 'class' / cls / 'class.json'
    if material.is_file():
        # Signature and reference types found by the class material (write_class_material).
        wanted += json.loads(material.read_text()).get('referenced_classes', [])
    for p in packs:
        for r in p.get('references', []):
            for cn in r.get('community_names', [])[:1]:
                owner = owning_class(cn['name'])
                if owner:
                    wanted.append(owner.split('::')[-1])
    out = []
    for c in dict.fromkeys(wanted):
        if c != cls and c in headers:
            out.append((c, headers[c]))
    return out


def brief_sections(cls, packs, functions, root=None):
    """Shared headers, cookbook rules and sibling pointers for one class's functions."""
    root = Path(root or REPO)
    t = analysis_tables()
    classes = t[2] if t else {}
    lines = ['', ORIGIN_LINE]
    hdrs = shared_headers(cls, packs, repository_headers(root), classes)
    if hdrs:
        lines += ['', 'Shared headers (existing; include with `#include "<area>/<Class>.h"` instead of declaring '
                  'a stand-in, never edit them; if one lacks a member or virtual slot you need, declare your own '
                  'stand-in instead and say `header-gap <Class>` in your result line):']
        lines += [f'- `{c}`: `reconstruction/{h}`' for c, h in hdrs]
    by_rva = {p['rva_hex']: p for p in packs}
    rules = []
    for f in functions:
        listing = REPO / f.get('pack', '') / 'listing.txt' if f.get('pack') else None
        text = listing.read_text() if listing and listing.is_file() else ''
        for k in listing_traits(text, dict(f, **{'community_name': f.get('community_name')
                                                  or (by_rva.get(f['rva'], {}).get('identity') or {}).get(
                                                      'community_name')})):
            if k not in rules:
                rules.append(k)
    if rules:
        lines += ['', f'Cookbook rules these listings point to (`{COOKBOOK}`):']
        lines += [f'- {COOKBOOK_RULES[k]}' for k in rules]
    sib = sibling_lines(cls, [int(f['rva'], 16) if isinstance(f['rva'], str) else f['rva'] for f in functions],
                        limit=6)
    lines += sib
    return lines


def parse_list_line(line, build_id):
    """(rva, task id, unit, recipe, group, budget) from one list-file line."""
    parts = line.split()
    build, rva, task_id = parts[0], int(parts[1], 0), parts[2]
    if build != build_id:
        raise SystemExit(f'{build}: only the pinned build {build_id} has packs; addresses never transfer between builds')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', task_id):
        raise SystemExit(f'task id {task_id}: attempt accepts only [a-z0-9][a-z0-9.-]*')
    unit = recipe = group = budget = None
    for tok in parts[3:]:
        if tok.startswith('recipe='):
            recipe = tok[len('recipe='):]
        elif tok.startswith('group='):
            group = tok[len('group='):]
            if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', group):
                raise SystemExit(f'group {group}: task directories are [a-z0-9][a-z0-9.-]*')
        elif tok.startswith('budget='):
            budget = int(tok[len('budget='):])
        else:
            unit = tok
    return rva, task_id, unit, recipe, group, budget


GROUP_SCHEMA = 1


def write_group(gdir, unit_dirs):
    """group.json and BRIEF.md of a multi-unit task: one task directory per unit below `gdir`, each
    attempted and reported on its own, one Drafter for all of them."""
    units = []
    for d in unit_dirs:
        task = json.loads((Path(d) / 'task.json').read_text())
        units.append({'dir': Path(d).name, 'task_id': task['task_id'], 'compiled': task['compiled'],
                      'functions': [f['rva'] for f in task['functions'] if f.get('role') != 'regression'],
                      'bytes': sum(f['size'] or 0 for f in task['functions'] if f.get('role') != 'regression'),
                      'max_attempts': task['max_attempts']})
    group = {'group_schema': GROUP_SCHEMA, 'group_id': Path(gdir).name, 'units': units,
             'functions': sum(len(u['functions']) for u in units),
             'max_attempts': sum(u['max_attempts'] or 0 for u in units)}
    (Path(gdir) / 'group.json').write_text(json.dumps(group, indent=2) + '\n')
    (Path(gdir) / 'BRIEF.md').write_text(render_group_brief(group, Path(gdir)))
    return group


def render_group_brief(group, gdir):
    gid = group['group_id']
    lines = [f'# Brief: {gid} (small task: {len(group["units"])} units, {group["functions"]} functions)', '',
             'One translation unit per class, each in its own task directory below this one. Attempt and report',
             'each unit separately: `tools/verifier/attempt .local/tasks/' + gid + '/<dir>`; the budget printed as',
             '`counted N/M` is per unit. `tools/verifier/attempt .local/tasks/' + gid + '` prints every unit\'s state.',
             'Work through the units in the order below (smallest first). The units share a family base: declare',
             'the same stand-in for it, with the same names and labels, in every unit that needs it, or include its',
             'existing header where one is listed. Result lines go to `.local/handoffs/' + gid + '.jsonl` (one per',
             'function, then one task line per unit with its `task` id).', '',
             '| dir | unit | functions | bytes | budget |', '|---|---|---|---|---|']
    for u in sorted(group['units'], key=lambda u: (u['bytes'], u['dir'])):
        lines.append(f'| `{u["dir"]}` | `{u["compiled"]}` | {len(u["functions"])} | {u["bytes"]} | {u["max_attempts"]} |')
    lines += ['', f'Total budget {group["max_attempts"]} counted attempts over all units.',
              'Class and member names are COMMUNITY (unverified); do not edit other units or the listed shared headers.',
              ORIGIN_LINE, '']
    # The per-unit briefs repeat the same generic lines; the group brief keeps them once (above).
    generic = ('Known risks:', 'Order (smallest first)', '- Class and member names', '- Declare other classes',
               'Body origin:')
    for u in sorted(group['units'], key=lambda u: (u['bytes'], u['dir'])):
        text = (gdir / u['dir'] / 'BRIEF.md').read_text().splitlines()
        lines += [f'## {u["dir"]}', '']
        for ln in text[2:]:
            if ln.startswith(generic) or (not ln.strip() and (not lines[-1].strip())):
                continue
            # Unit sections are level 2 here, so a unit brief's own level-2 headings move down one.
            lines.append('#' + ln if ln.startswith('## ') else ln)
        lines.append('')
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------------------------
# plan: propose class-grouped units from the community-named survey.

MIDDLEWARE = re.compile(r'^(GFx\w*|GAS\w*|Scaleform|hk[A-Z]\w*|Bink\w*|SKSE|REL|stl|std|WinAPI)$')
KIND_ORDER = ('form', 'extra-data', 'netimmerse', 'bs-utility', 'menu-ui', 'magic-effect', 'actor',
              'manager-singleton')
BENIGN_CAUTION = 'no-pdata: leaf'


def class_kind(cls, area, has_singleton, bases=()):
    if cls.startswith('Extra'):
        return 'extra-data'
    if re.search(r'Menu|HUD|Hud|^UI[A-Z]|^UI$', cls):
        return 'menu-ui'
    if area == 'actors':
        return 'actor'
    if re.match(r'(Magic|ActiveEffect|Spell|Enchant|Effect)', cls) or cls.endswith('Effect'):
        return 'magic-effect'
    if cls.startswith('Ni') and cls[2:3].isupper():
        return 'netimmerse'
    if has_singleton or re.search(r'(Manager|Interface)$', cls):
        return 'manager-singleton'
    if 'TESForm' in bases or cls == 'TESForm':
        # The prefix rule files TESFile and other non-forms under forms/ too; RTTI tells forms apart.
        return 'form'
    if area == 'inventory' or cls.startswith('Inventory'):
        return 'inventory'
    if cls.startswith('BS') and cls[2:3].isupper():
        return 'bs-utility'
    return 'other'


def pick_functions(elig, per_class, min_big, big_bytes, max_unit_bytes):
    """Up to per_class functions: the smallest `min_big` over big_bytes, then the smallest others."""
    elig = sorted(elig, key=lambda f: (f['size'], f['rva']))
    big = [f for f in elig if f['size'] > big_bytes][:min_big]
    rest = [f for f in elig if f not in big]
    chosen = big + rest[:max(0, per_class - len(big))]
    if len(chosen) < per_class:
        chosen += [f for f in elig if f not in chosen][:per_class - len(chosen)]
    chosen.sort(key=lambda f: (f['size'], f['rva']))
    while sum(f['size'] for f in chosen) > max_unit_bytes and len(chosen) > 1:
        chosen.pop()  # drop the largest until the unit is a sensible size
    return chosen


def plan_candidates(rows, accepted, existing_units, area_overrides, extend, opts, comms, bases_of=lambda c: ()):
    """Group survey rows by owning class and apply the selection criteria.

    rows: dicts with rva, size, verdict, cautions, name, how, origin. Returns ({class: info}, rejections)
    where rejections counts functions per reason."""
    rejected, classes = {}, {}

    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1

    ng = comms[0]
    for r in rows:
        if not r['name']:
            reject('no community name')
            continue
        if 'NG' not in r['origin']:
            reject('named only by the GPL fork')
            continue
        parts = [p for p in r['name'].split('::') if p]
        cls = owning_class(r['name'])
        if not cls:
            reject('free function (no owning class)')
            continue
        if any(MIDDLEWARE.match(p) for p in parts[:-1]):
            reject('middleware or non-engine namespace')
            continue
        if r['verdict'] == 'unsupported':
            reject('unsupported by comparator v2')
            continue
        if r['verdict'] == 'caution' and any(not c.startswith(BENIGN_CAUTION) for c in r['cautions']):
            reject('caution other than a padded leaf without .pdata')
            continue
        if r['size'] > opts['max_function_bytes']:
            reject(f'over {opts["max_function_bytes"]} bytes')
            continue
        info = classes.setdefault(cls, {'class': cls, 'functions': [], 'regression': [], 'notes': []})
        if r['rva'] in accepted:
            info['regression'].append(r)
            continue
        info['functions'].append(r)
    out = {}
    for cls, info in classes.items():
        ex = ng.class_excerpt(cls, limit=6000)
        if not ex:
            for r in info['functions']:
                reject('class not defined in NG headers')
            continue
        body = ex['text']
        declared = []
        for r in info['functions']:
            method = r['name'].split('::')[-1]
            if re.search(r'\b' + re.escape(method) + r'\s*\(', body):
                declared.append(r)
            else:
                reject('method not declared in the NG class body (enclosing-name doubt)')
        info['functions'] = declared
        existing = existing_units.get(cls)
        area = area_overrides.get(cls) or (existing.split('/')[1] if existing else None) or area_for(cls)
        info['area'] = area
        info['unit'] = existing or (f'reconstruction/{area}/{cls}.cpp' if area else None)
        info['existing_unit'] = bool(existing)
        info['kind'] = class_kind(cls, area, bool(re.search(r'\bGetSingleton\s*\(', body)), bases_of(cls))
        info['eligible'] = len(declared)
        if len(declared) < opts['min_functions']:
            info['status'] = f'fewer than {opts["min_functions"]} eligible functions'
        elif not area:
            info['status'] = 'no area rule (reconstruction/README.md rule 3: ask first)'
        elif existing and cls != extend:
            info['status'] = 'extends an existing unit (re-opens its records); not the chosen extension'
        else:
            info['status'] = 'candidate'
        info['picked'] = pick_functions(declared, opts['per_class'], opts['min_big'], opts['big_bytes'],
                                        opts['max_unit_bytes'])
        info['score'] = (len(declared) >= opts['min_functions'],
                         min(sum(1 for f in declared if f['size'] > opts['big_bytes']), opts['min_big']),
                         sum(1 for f in declared if f['how'] == 'table'), len(declared))
        out[cls] = info
    return out, rejected


def plan_select(cands, n_classes, extend):
    """One class per kind in KIND_ORDER (the extension forced into its kind), then the best of the rest."""
    ok = {c: i for c, i in cands.items() if i['status'] == 'candidate'}
    chosen, missing = [], []
    for kind in KIND_ORDER:
        pool = sorted((i for i in ok.values() if i['kind'] == kind and i['class'] not in chosen),
                      key=lambda i: (i['class'] != extend, tuple(-x for x in i['score']), i['class']))
        if extend in ok and ok[extend]['kind'] == kind and extend not in chosen:
            pool.sort(key=lambda i: i['class'] != extend)
        if pool:
            chosen.append(pool[0]['class'])
        else:
            missing.append(kind)
    if extend in ok and extend not in chosen:
        chosen.append(extend)
    rest = sorted((i for i in ok.values() if i['class'] not in chosen),
                  key=lambda i: (tuple(-x for x in i['score']), i['class']))
    used = {ok[c]['kind'] for c in chosen}
    # Fill from kinds not yet used first, so the batch stays varied.
    rest.sort(key=lambda i: i['kind'] in used)
    chosen += [i['class'] for i in rest[:max(0, n_classes - len(chosen))]]
    return chosen[:n_classes], missing


def cmd_plan(args):
    cfg = load_config(args.config)
    target, img, addrlib, comms = setup(cfg)
    survey = Path(args.survey or REPO / '.local/packs/_survey' / f'{target["build_id"]}-named')
    gmeta, grefs = load_ghidra(survey / 'ghidra')
    progress = json.loads((REPO / 'data/progress.json').read_text())
    # Entries citing --reuse-evidence came from this plan earlier; counting them as claimed would make
    # a re-run propose a different batch instead of reproducing the recorded one.
    claimed = {fn['rva'] for fn in progress['functions'] if fn['build_id'] == target['build_id']
               and fn['evidence'] not in (args.reuse_evidence or [])}
    accepted = {fn['rva'] for fn in progress['functions'] if fn['status'] == 'matched'}
    existing_units = {p.stem: p.relative_to(REPO).as_posix() for p in (REPO / 'reconstruction').glob('*/*.cpp')}
    rows = []
    for rva in sorted(gmeta):
        fact = classify(img, addrlib, comms, rva, gmeta[rva], grefs.get(rva, []))
        ident, _ = community_identity(comms, addrlib['by_rva'].get(rva, []))
        if rva in claimed and rva not in accepted:
            continue  # already in the inventory for another task
        rows.append({'rva': rva, 'size': fact.get('size') or 0, 'verdict': fact['verdict'],
                     'cautions': fact['cautions'], 'reasons': fact['reasons'],
                     'name': short_name(ident['name']) if ident else None,
                     'how': ident['how'] if ident else None, 'origin': ident['origin'] if ident else '',
                     'refs': fact.get('reference_counts', {}),
                     'imports': sum(1 for r in fact.get('references', []) if r['resolution'] == 'import')})
    overrides = dict(a.split('=', 1) for a in args.area or [])
    opts = {'min_functions': args.min_functions, 'per_class': args.per_class, 'min_big': 2,
            'big_bytes': 100, 'max_function_bytes': args.max_function_bytes, 'max_unit_bytes': args.max_unit_bytes}
    vt_ids = vtable_index(comms)
    by_id = {i: rva for rva, ids in addrlib['by_rva'].items() for i in ids}

    def bases_of(cls):
        own = by_id.get(vt_ids.get(cls))
        return [b.split('__')[-1] for b in rtti_bases(img, own)] if own is not None else []
    cands, rejected = plan_candidates(rows, accepted, existing_units, overrides, args.extend, opts, comms, bases_of)
    for cls in args.exclude or []:
        if cls in cands:
            cands[cls]['status'] = 'excluded by the operator'
    chosen, missing = plan_select(cands, args.classes, args.extend)
    if args.total:
        # Short classes leave the batch under the requested total: grow, one function at a time, the
        # class with the most eligible functions left, never past per_class + 2.
        while sum(len(cands[x]['picked']) for x in chosen) < args.total:
            growable = []
            for c in chosen:
                info = cands[c]
                if len(info['picked']) >= args.per_class + 2:
                    continue
                grown = pick_functions(info['functions'], len(info['picked']) + 1, opts['min_big'],
                                       opts['big_bytes'], opts['max_unit_bytes'])
                if len(grown) > len(info['picked']):
                    growable.append((-(info['eligible'] - len(info['picked'])), len(info['picked']), c, grown))
            if not growable:
                break
            _, _, c, grown = min(growable)
            cands[c]['picked'] = grown
    # Statistics for sizing later batches: supported named functions per class.
    sup = [r for r in rows if r['verdict'] != 'unsupported' and r['name'] and owning_class(r['name'])]
    per_class = {}
    for r in sup:
        per_class[owning_class(r['name'])] = per_class.get(owning_class(r['name']), 0) + 1
    hist = {}
    for n in per_class.values():
        b = '1' if n == 1 else '2-3' if n <= 3 else '4-5' if n <= 5 else '6-9' if n <= 9 else '10+'
        hist[b] = hist.get(b, 0) + 1
    all_named = [r for r in rows if r['name']]
    stats = {
        'ng_named_functions': len(all_named),
        'supported': sum(1 for r in all_named if r['verdict'] == 'supported'),
        'caution': sum(1 for r in all_named if r['verdict'] == 'caution'),
        'unsupported': sum(1 for r in all_named if r['verdict'] == 'unsupported'),
        'supported_or_caution_with_owning_class': len(sup),
        'classes_with_supported': len(per_class),
        'classes_with_at_least_4_supported': sum(1 for n in per_class.values() if n >= 4),
        'class_size_histogram': {k: hist.get(k, 0) for k in ('1', '2-3', '4-5', '6-9', '10+')},
        'functions_in_classes_by_size': {
            k: sum(n for n in per_class.values()
                   if (k == '1' and n == 1) or (k == '2-3' and 2 <= n <= 3) or (k == '4-5' and 4 <= n <= 5)
                   or (k == '6-9' and 6 <= n <= 9) or (k == '10+' and n >= 10))
            for k in ('1', '2-3', '4-5', '6-9', '10+')},
        'classes_meeting_all_plan_criteria': sum(1 for i in cands.values() if i['status'] == 'candidate'),
        'eligible_functions_in_those_classes': sum(i['eligible'] for i in cands.values()
                                                   if i['status'] == 'candidate')}
    out_dir = REPO / '.local/packs/_plan' / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    list_lines = ['# build id         rva        task id                         unit',
                  f'# generated by export_pack.py plan ({args.label}); review before running packs']
    for c in chosen:
        info = cands[c]
        for f in info['picked']:
            # Task ids are lowercase (tools/verifier/pipeline.py load_task); the class keeps its case in the unit.
            list_lines.append(f'{target["build_id"]}  0x{f["rva"]:x}  {(args.task_prefix + c).lower()}  {info["unit"]}')
    (out_dir / 'list.txt').write_text('\n'.join(list_lines) + '\n')

    def brief_fn(f):
        return {'rva': hex(f['rva']), 'size': f['size'], 'name': f['name'], 'how': f['how'], 'verdict': f['verdict'],
                'refs': f['refs'], 'imports': f['imports']}
    plan = {'build_id': target['build_id'], 'survey': str(survey.relative_to(REPO)), 'criteria': opts | {
                'extend': args.extend, 'area_overrides': overrides, 'kinds': KIND_ORDER,
                'excluded': args.exclude or []},
            'chosen': [{'class': c, 'kind': cands[c]['kind'], 'unit': cands[c]['unit'],
                        'existing_unit': cands[c]['existing_unit'], 'eligible': cands[c]['eligible'],
                        'functions': [brief_fn(f) for f in cands[c]['picked']],
                        'bytes': sum(f['size'] for f in cands[c]['picked']),
                        'regression': [hex(f['rva']) for f in cands[c]['regression']]} for c in chosen],
            'kinds_without_candidate': missing,
            'other_classes': sorted(({'class': c, 'kind': i['kind'], 'eligible': i['eligible'], 'status': i['status'],
                                      'area': i['area']} for c, i in cands.items() if c not in chosen),
                                    key=lambda d: (-d['eligible'], d['class'])),
            'function_rejections': dict(sorted(rejected.items(), key=lambda kv: -kv[1])),
            'stats': stats}
    (out_dir / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for c in plan['chosen']:
        print(f'{c["class"]:28s} {c["kind"]:18s} {c["unit"]:48s} {len(c["functions"])} fns {c["bytes"]} B '
              + ' '.join(str(f['size']) for f in c['functions']) + (' +regression' if c['regression'] else ''))
    print('kinds without a candidate:', ', '.join(missing) or 'none')
    print('runners-up:', ', '.join(f'{d["class"]}({d["kind"]},{d["eligible"]},{d["status"][:24]})'
                                   for d in plan['other_classes'] if d['eligible'] >= 3)[:1200])
    print(json.dumps(stats))
    print(f'wrote {out_dir.relative_to(REPO)}/list.txt and plan.json')


# ---------------------------------------------------------------------------------------------
# plan --order fanin: whole-image ordering from build_function_table.py.

OUT_OF_SCOPE_AREAS = {'havok', 'scaleform', 'std', 'bnet'}
SIZE_BUCKETS = ((32, '<=32'), (64, '33-64'), (128, '65-128'), (256, '129-256'), (512, '257-512'), (None, '>512'))
NAME_ORDER = {'ng-slot': 0, 'ng-id': 1, 'po3-slot': 2, 'po3-id': 3, 'meh321': 4}


def size_bucket(n):
    for hi, label in SIZE_BUCKETS:
        if hi is None or n <= hi:
            return label


def usable_names(row):
    """Names a plan may use: checked slot names, and id names that are not placeholders and do not
    contradict the image's vftables. Sorted NG first (MIT), then po3, then meh321."""
    out = [n for n in row.get('names', []) if n['how'] != 'placeholder' and n.get('agrees_with_vtable') is not False
           and re.fullmatch(r'[A-Za-z_~][\w:~]*', n['name'] or '')]
    return sorted(out, key=lambda n: NAME_ORDER.get(n['source'], 9))


def v2_ready(row):
    """Supported by comparator v2, or cautioned only for things a Drafter handles: a padded leaf
    without .pdata, or funclets whose references bind by position."""
    v = row.get('v2') or {}
    if v.get('verdict') == 'supported':
        return True
    if v.get('verdict') != 'caution':
        return False
    benign = ('no-pdata', 'funclet code references are not listed')
    return all(c.startswith(benign) for c in v.get('cautions', []))


def table_eligibility(row, classes, claimed, max_bytes=None):
    """None when the function may be planned, else the first reason it may not."""
    if row['kind'] != 'ordinary':
        return 'not an ordinary function (' + row['kind'] + ')'
    if not v2_ready(row):
        return 'not supported by comparator v2'
    if row['rva'] in claimed:
        return 'already in the inventory'
    if not usable_names(row):
        return 'no usable name from an approved source'
    owner = row.get('owner') or {}
    cls = owner.get('class')
    if not cls or owner.get('how') == 'rtti-adjacent':
        return 'no owning class'
    c = classes.get(cls)
    if c is None:
        return 'class has no primary vftable to check'
    if not c.get('passes'):
        return 'class fails the per-class checks'
    if c['area'] in OUT_OF_SCOPE_AREAS:
        return 'middleware or std area'
    if '<' in cls or '::' in cls:
        return 'template or nested class (no unit name rule)'
    if area_for(cls) is None:
        return 'no area rule for the class (reconstruction/README.md rule 3)'
    if area_for(cls) == 'actors' and c['area'] in ('netimmerse', 'bsengine'):
        # `*Process` would file a library class (NiCullingProcess) under actors; ask before using it.
        return 'area rules disagree (library prefix and *Process)'
    if max_bytes and (row['size'] or 0) > max_bytes:
        return f'over {max_bytes} bytes'
    return None


def inventory_row(row, target, evidence, owner_name='awarebayes'):
    n = usable_names(row)[0]
    src = {'ng-slot': 'CharmedBaryon/CommonLibSSE-NG commit {ng} (MIT), virtual slot comment of the class header, '
                      'joined through the image RTTI vftable slot {slot}',
           'po3-slot': 'powerof3/CommonLibSSE commit {po3} (GPL-3.0), virtual slot comment of the class header, '
                       'joined through the image RTTI vftable slot {slot}',
           'ng-id': 'CharmedBaryon/CommonLibSSE-NG commit {ng} (MIT), joined through Address Library id {ae}',
           'po3-id': 'powerof3/CommonLibSSE commit {po3} (GPL-3.0), joined through Address Library id {ae}',
           'meh321': 'meh321 Address Library name list (used with the author\'s permission as reported by the '
                     'maintainer), Address Library id {ae}'}[n['source']]
    owner = row.get('owner') or {}
    name = n['name']
    if n['source'].endswith('-slot') and owner.get('class'):
        name = owner['class'] + '::' + name.split('::')[-1]
    return {'id': f'{target["build_id"]}-{hex(row["rva"])}', 'build_id': target['build_id'], 'rva': row['rva'],
            'size': row['size'], 'status': 'mapped', 'name': name, 'name_origin': 'COMMUNITY',
            'name_source': 'Community name, not verified: ' + src.format(
                ng=target.get('ng_revision', ''), po3=target.get('po3_revision', ''), slot=owner.get('slot'),
                ae=n.get('ae_id')) + f'. RVA {hex(row["rva"])}; size from the comparator v2 extent.',
            'owner': owner_name, 'evidence': evidence}


def plan_from_table(rows, classes, claimed, opts):
    """Order and pick a batch: classes that pass the checks, functions by fan-in then size, one
    function per L1 cluster, a quota of C++ EH functions with few states."""
    elig, rejected = [], Counter()
    for r in rows:
        why = table_eligibility(r, classes, claimed)
        if why:
            rejected[why] += 1
        else:
            elig.append(r)
    stats = {'eligible_any_size': len(elig),
             'eligible_by_size': dict(Counter(size_bucket(r['size'] or 0) for r in elig)),
             'eligible_by_first_name_source': dict(Counter(usable_names(r)[0]['source'] for r in elig)),
             'eligible_named_by_source': {s: sum(1 for r in elig if any(n['source'] == s for n in usable_names(r)))
                                          for s in NAME_ORDER},
             'eligible_with_cxx_eh': sum(1 for r in elig if r['eh'].get('handler_kind') == 'c++'),
             'eligible_classes': len({r['owner']['class'] for r in elig}),
             'rejections': dict(rejected.most_common())}
    small = [r for r in elig if (r['size'] or 0) <= opts['max_function_bytes']]

    def is_eh(r):
        return r['eh'].get('handler_kind') == 'c++' and r['eh'].get('states') and \
            r['eh']['states'] <= opts['max_eh_states'] and not r['eh'].get('try_blocks')

    by_class = defaultdict(list)
    for r in small:
        by_class[r['owner']['class']].append(r)

    def fn_key(r):
        return (-min(r['callers'], 50), r['size'] or 0, r['rva'])

    def class_score(c, fs):
        return (sum(min(f['callers'], 50) for f in fs) + 5 * len(fs), -sum(f['size'] or 0 for f in fs))

    # A class with an accepted unit is extended only on request: editing it re-opens its records.
    skip = set(opts.get('existing_units', ())) - {opts.get('extend')}
    for c in skip & set(by_class):
        stats.setdefault('skipped_existing_unit', []).append(c)
    by_class = {c: fs for c, fs in by_class.items() if c not in skip}
    cands = [(class_score(c, fs), c) for c, fs in by_class.items() if len(fs) >= opts['min_functions']]
    cands.sort(key=lambda x: (tuple(-v for v in x[0]), x[1]))
    chosen, per_area = [], Counter()
    for _, c in cands:
        area = classes[c]['area']
        if per_area[area] >= opts['max_classes_per_area']:
            continue
        chosen.append(c)
        per_area[area] += 1
        if len(chosen) >= opts['classes']:
            break
    picked, clusters = {}, set()
    non_eh_quota = opts['total'] - opts['eh']
    per_class = max(1, -(-non_eh_quota // max(1, len(chosen))))
    for c in chosen:
        got = []
        # C++ EH functions come only through the quota below, and only with few states.
        for r in sorted((f for f in by_class[c] if f['eh'].get('handler_kind') != 'c++'), key=fn_key):
            if r['l1'] in clusters:
                continue
            got.append(r)
            clusters.add(r['l1'])
            if len(got) >= per_class:
                break
        picked[c] = got
    while sum(len(v) for v in picked.values()) > non_eh_quota:
        c = max(picked, key=lambda k: (len(picked[k]), k))
        clusters.discard(picked[c].pop()['l1'])
    eh_pool = sorted((f for c in chosen for f in by_class[c] if is_eh(f) and f['l1'] not in clusters),
                     key=lambda r: (r['eh']['states'], fn_key(r)))
    extra_classes = []
    if len(eh_pool) < opts['eh']:
        others = sorted((f for c, fs in by_class.items() if c not in chosen for f in fs if is_eh(f)),
                        key=lambda r: (r['eh']['states'], fn_key(r)))
        eh_pool += others
    n_eh = 0
    for r in eh_pool:
        if n_eh >= opts['eh']:
            break
        if r['l1'] in clusters:
            continue
        c = r['owner']['class']
        if c not in picked:
            picked[c] = []
            extra_classes.append(c)
        picked[c].append(r)
        clusters.add(r['l1'])
        n_eh += 1
    stats['eh_picked'] = n_eh
    stats['eh_pool_in_chosen_classes'] = sum(1 for c in chosen for f in by_class[c] if is_eh(f))
    return chosen + extra_classes, picked, stats


def cmd_plan_table(args):
    cfg = load_config(args.config)
    target = json.loads((REPO / 'builds/target.json').read_text())
    t0 = time.monotonic()
    t = analysis_tables(args.table)
    if not t:
        raise SystemExit(f'no function table under {args.table or ANALYSIS}; run tools/ghidra/build_function_table.py')
    fns, _, classes, meta = t
    progress = json.loads((REPO / 'data/progress.json').read_text())
    claimed = {fn['rva'] for fn in progress['functions'] if fn['build_id'] == target['build_id']}
    opts = {'classes': args.classes, 'total': args.total or 150, 'eh': args.eh, 'max_eh_states': args.max_eh_states,
            'min_functions': args.min_functions, 'max_function_bytes': args.max_function_bytes,
            'max_classes_per_area': args.max_classes_per_area, 'extend': args.extend,
            'existing_units': sorted(p.stem for p in (REPO / 'reconstruction').glob('*/*.cpp'))}
    order, picked, stats = plan_from_table(list(fns.values()), classes, claimed, opts)
    target = dict(target, ng_revision=cfg['ng_revision'], po3_revision=cfg.get('po3_revision', ''))
    out_dir = REPO / '.local/packs/_plan' / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence = args.evidence
    lines = ['# build id         rva        task id                         unit',
             f'# generated by export_pack.py plan --order fanin ({args.label}); review before running packs']
    inventory, chosen = [], []
    for c in order:
        fs = sorted(picked.get(c, []), key=lambda r: (r['size'] or 0, r['rva']))
        if not fs:
            continue
        unit = f'reconstruction/{area_for(c)}/{c}.cpp'
        existing = sorted((REPO / 'reconstruction').glob(f'*/{c}.cpp'))
        if existing:
            unit = existing[0].relative_to(REPO).as_posix()
        for r in fs:
            lines.append(f'{target["build_id"]}  0x{r["rva"]:x}  {(args.task_prefix + c).lower()}  {unit}')
            inventory.append(inventory_row(r, target, evidence))
        cl = classes[c]
        chosen.append({'class': c, 'area': cl['area'], 'unit': unit, 'size': cl.get('size'),
                       'checks_passed_by': cl['passes'], 'vftable_slots': len(cl['slots']),
                       'functions': [{'rva': hex(r['rva']), 'size': r['size'], 'callers': r['callers'],
                                      'name': usable_names(r)[0]['name'], 'name_source': usable_names(r)[0]['source'],
                                      'eh_states': r['eh'].get('states'), 'verdict': r['v2']['verdict'],
                                      'cluster_size': r.get('cluster_size')} for r in fs]})
    (out_dir / 'list.txt').write_text('\n'.join(lines) + '\n')
    (out_dir / 'inventory-rows.json').write_text(json.dumps(inventory, indent=2) + '\n')
    plan = {'build_id': target['build_id'], 'order': 'fanin', 'table': meta.get('inputs'), 'criteria': opts,
            'chosen': chosen, 'stats': stats, 'functions': len(inventory),
            'eh_functions': sum(1 for c in chosen for f in c['functions'] if f['eh_states']),
            'bytes': sum(f['size'] or 0 for c in chosen for f in c['functions']),
            'python_s': round(time.monotonic() - t0, 1)}
    (out_dir / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for c in chosen:
        print(f'{c["class"]:32s} {c["area"]:10s} {len(c["functions"])} fns '
              + ' '.join(f'{f["size"]}{"e" if f["eh_states"] else ""}' for f in c['functions']))
    print(json.dumps({k: v for k, v in stats.items() if k != 'rejections'}))
    print(f'{len(inventory)} functions in {len(chosen)} classes; wrote {out_dir.relative_to(REPO)}/list.txt, '
          'plan.json, inventory-rows.json')


def open_task_classes(task_root):
    """Classes whose unit some task directory under `task_root` (one or two levels deep) compiles."""
    out = set()
    for tj in list(Path(task_root).glob('*/task.json')) + list(Path(task_root).glob('*/*/task.json')):
        try:
            out.add(Path(json.loads(tj.read_text())['compiled']).stem)
        except (OSError, ValueError, KeyError):
            continue
    return out


def cmd_plan_cheap(args):
    import plan_cheap
    cfg = load_config(args.config)
    target = json.loads((REPO / 'builds/target.json').read_text())
    t0 = time.monotonic()
    t = analysis_tables(args.table)
    if not t:
        raise SystemExit(f'no function table under {args.table or ANALYSIS}; run tools/ghidra/build_function_table.py')
    fns, _, classes, meta = t
    progress = json.loads((REPO / 'data/progress.json').read_text())
    claimed = {fn['rva'] for fn in progress['functions'] if fn['build_id'] == target['build_id']}
    blob = Path(cfg['image']).read_bytes()
    if sha256_bytes(blob) != target['image_sha256']:
        raise SystemExit('image SHA-256 differs from builds/target.json')
    pe = PeImage(blob)
    parked = set()
    for path in args.parked or []:
        census = json.loads(Path(path).read_text())
        for key in ('skip', 'm2_noh'):
            parked.update(census.get(key, []))
    units = {p.stem for p in (REPO / 'reconstruction').glob('*/*.cpp')}
    material = {p.name for p in (REPO / '.local/packs' / target['build_id'] / 'class').glob('*') if p.is_dir()}
    skip = units | open_task_classes(REPO / '.local/tasks') | material | set(args.exclude or [])
    sib = sibling_index(args.table) or {'by_rva': {}}
    fnv_rvas = set(sib['by_rva'])
    fnv_o2 = {rva for rva, hits in sib['by_rva'].items() if any(r.get('opt') == '/O2' for r, _ in hits)}
    catalogue = set(json.loads(Path(args.catalogue).read_text())) if args.catalogue else set()
    headers = {p.stem for p in (REPO / 'reconstruction').glob('*/*.h')}
    rows = list(fns.values())
    # Only rows that pass the cheaper checks are scanned for thread-local reads.
    pre = [r for r in rows if not table_eligibility(r, classes, claimed, args.max_function_bytes)]
    tls = plan_cheap.tls_rvas(lambda rva, n: pe.read(rva, n, 'function')[1], pre)
    opts = {'total': args.total or 232, 'max_function_bytes': args.max_function_bytes, 'parked': parked,
            'tls': tls, 'skip_classes': skip, 'fnv_rvas': fnv_rvas, 'fnv_o2_rvas': fnv_o2,
            'catalogue': catalogue, 'headers': headers, 'task_prefix': args.task_prefix}
    if args.normal_functions is not None:
        opts['normal_functions'] = args.normal_functions
    tasks, stats = plan_cheap.plan(rows, classes, claimed, opts, table_eligibility)
    stats['tls_scanned'], stats['tls_found'], stats['parked_rvas'] = len(pre), len(tls), len(parked)
    target = dict(target, ng_revision=cfg['ng_revision'], po3_revision=cfg.get('po3_revision', ''))
    out_dir = REPO / '.local/packs/_plan' / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ['# build id         rva        task id                         unit  [group=<task dir>] budget=<n>',
             f'# generated by export_pack.py plan --order cheap ({args.label}); review before running packs']
    inventory, plan_tasks = [], []
    for tk in tasks:
        entry = {'id': tk['id'], 'kind': tk['kind'], 'family': tk['family'], 'budget': tk['budget'],
                 'score': round(tk['score'], 2), 'units': []}
        for u in tk['units']:
            c = u['class']
            unit = f'reconstruction/{area_for(c)}/{c}.cpp'
            group = f' group={tk["id"]}' if tk['kind'] == 'small' else ''
            for r in u['functions']:
                lines.append(f'{target["build_id"]}  0x{r["rva"]:x}  {u["task_id"]}  {unit}{group} budget={u["budget"]}')
                inventory.append(inventory_row(r, target, args.evidence))
            entry['units'].append({'class': c, 'task_id': u['task_id'], 'unit': unit, 'budget': u['budget'],
                                   'functions': [{'rva': hex(r['rva']), 'size': r['size'], 'callers': r['callers'],
                                                  'name': usable_names(r)[0]['name'],
                                                  'name_source': usable_names(r)[0]['source'],
                                                  'fnv': r['rva'] in fnv_rvas, 'cluster_size': r.get('cluster_size'),
                                                  'score': round(r['_score'], 2)} for r in u['functions']]})
        plan_tasks.append(entry)
    comp = plan_cheap.composition(tasks, classes, fnv_rvas, area_for)
    (out_dir / 'list.txt').write_text('\n'.join(lines) + '\n')
    (out_dir / 'inventory-rows.json').write_text(json.dumps(inventory, indent=2) + '\n')
    plan = {'build_id': target['build_id'], 'order': 'cheap', 'table': meta.get('inputs'),
            'criteria': {k: (sorted(v) if isinstance(v, set) and len(v) < 50 else
                             (f'{len(v)} entries' if isinstance(v, set) else v)) for k, v in opts.items()},
            'tasks': plan_tasks, 'stats': stats, 'composition': comp,
            'python_s': round(time.monotonic() - t0, 1)}
    (out_dir / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for e in plan_tasks:
        print(f'{e["id"]:44s} {e["kind"]:6s} units {len(e["units"]):2d} functions '
              f'{sum(len(u["functions"]) for u in e["units"]):2d} budget {e["budget"]}')
    print(json.dumps({'stats': {k: v for k, v in stats.items() if k != 'rejections'}, 'composition': comp}))
    print(f'wrote {out_dir.relative_to(REPO)}/list.txt, plan.json, inventory-rows.json')


# ---------------------------------------------------------------------------------------------
# bind: the shared implementation is tools/verifier/bind.py, which attempt runs on every compile.

def bind(task_dir, obj_path=None):
    sys.path.insert(0, str(REPO / 'tools' / 'verifier'))
    import bind as binding
    args = ['--task', str(task_dir)] + (['--object', str(obj_path)] if obj_path else [])
    return binding.main(args)


# ---------------------------------------------------------------------------------------------

def cmd_packs(args):
    cfg = load_config(args.config)
    t_setup = time.monotonic()
    target, img, addrlib, comms = setup(cfg)
    t_setup = time.monotonic() - t_setup
    rows, groups, budgets = [], {}, {}
    for line in Path(args.list).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        rva, task_id, unit, recipe, group, budget = parse_list_line(line, target['build_id'])
        rows.append((rva, task_id, unit, recipe))
        if group and task_id not in groups.setdefault(group, []):
            groups[group].append(task_id)
        if budget is not None:
            budgets[task_id] = budget
    run = REPO / '.local/packs/_runs' / time.strftime('%Y%m%dT%H%M%S')
    run.mkdir(parents=True, exist_ok=True)
    (run / 'rvas.txt').write_text(''.join('0x%x\n' % r for r, *_ in rows))
    t_ghidra = run_ghidra(cfg, str(run / 'rvas.txt'), run / 'ghidra', 'full', run / 'ghidra.log')
    gmeta, grefs = load_ghidra(run / 'ghidra')
    t0 = time.monotonic()
    packs, by_task, recipes, moved = {}, {}, {}, []
    for rva, task_id, unit, recipe in rows:
        fact = classify(img, addrlib, comms, rva, gmeta.get(rva), grefs.get(rva, []))
        pack = write_pack(REPO / '.local/packs' / target['build_id'] / hex(rva), fact, target, addrlib, comms,
                          run / 'ghidra', {'ghidra_share': round(t_ghidra / len(rows), 2)}, img)
        packs[rva] = pack
        recipes.setdefault(task_id, recipe or args.recipe)
        if recipes[task_id] != (recipe or recipes[task_id]):
            raise SystemExit(f'task {task_id}: one task is one recipe, got {recipes[task_id]} and {recipe}')
        by_task.setdefault(task_id, []).append((pack, unit))
        fp_eq = pack.get('fp_equality_without_parity')
        print(f'{hex(rva)} {pack["size"]} B {pack["verdict"]} {",".join(pack["reasons"])} '
              f'{pack["identity"]["community_name"]}' + (f' fp== without parity {fp_eq}' if fp_eq else ''))
    if args.fpfast != 'keep':
        # One unit has one recipe (reconstruction/README.md), and a second unit per class would need a
        # second class name (the lint ties a unit's file name to the class it declares). So a task with
        # a function showing the /fp:fast pattern takes the fp:fast recipe as a whole when its other
        # functions are recipe-neutral (no float arithmetic, compare or conversion); otherwise the
        # flagged functions leave the batch.
        for task_id, items in list(by_task.items()):
            if recipes[task_id] != args.recipe:
                continue
            flagged = [p for p, _ in items if p.get('fp_equality_without_parity')]
            if not flagged:
                continue
            listing = {p['rva_hex']: (REPO / '.local/packs' / target['build_id'] / p['rva_hex'] / 'listing.txt')
                       for p, _ in items}
            others = [p for p, _ in items if p not in flagged]
            if args.fpfast == 'unit' and not any(
                    fp_sensitive(listing[p['rva_hex']].read_text()) for p in others if listing[p['rva_hex']].is_file()):
                recipes[task_id] = args.fpfast_recipe
                moved += [(p['rva_hex'], task_id, 'unit recipe ' + args.fpfast_recipe) for p in flagged]
                print(f'task {task_id}: recipe {args.fpfast_recipe} (other functions are recipe-neutral)')
            else:
                by_task[task_id] = [(p, u) for p, u in items if p not in flagged]
                moved += [(p['rva_hex'], task_id, 'dropped') for p in flagged]
                print(f'task {task_id}: dropped ' + ', '.join(p['rva_hex'] for p in flagged))
    task_dirs = []
    for task_id, items in by_task.items():
        units = {u for _, u in items if u}
        if len(units) > 1:
            raise SystemExit(f'task {task_id}: one task is one unit, got {sorted(units)}')
        cls = items[0][0]['identity']['owning_class'] or 'Unknown'
        existing = sorted((REPO / 'reconstruction').glob(f'*/{cls}.cpp'))
        # A class already reconstructed keeps its unit: one pair per class (reconstruction/README.md).
        if not units and not existing and area_for(cls) is None:
            raise SystemExit(f'task {task_id}: no area rule covers class {cls}; name the unit in the list file '
                             '(reconstruction/README.md, "<area>")')
        unit = units.pop() if units else (existing[0].relative_to(REPO).as_posix() if existing
                                          else f'reconstruction/{area_for(cls)}/{cls}.cpp')
        group = next((g for g, ids in groups.items() if task_id in ids), None)
        root = REPO / '.local/tasks' / group if group else REPO / '.local/tasks'
        task_dirs.append(write_task(task_id, unit, recipes[task_id], [p for p, _ in items], target, root,
                                    budgets.get(task_id, args.max_attempts),
                                    None if task_id in budgets else args.attempts_per_function))
    if args.class_material:
        shared = write_class_material(task_dirs, target, img, addrlib, comms, args.shared_classes_name)
        for rva in packs:
            refresh_pack(REPO / '.local/packs' / target['build_id'] / hex(rva), target, img, addrlib, comms)
        print('classes used by more than one unit:', json.dumps(shared))
        for d in task_dirs:
            # The class material names the signature and reference types, which the brief's shared
            # header list reads, so briefs are written again once it exists.
            task = json.loads((d / 'task.json').read_text())
            mine = [packs[int(f['rva'], 16)] for f in task['functions'] if int(f['rva'], 16) in packs]
            (d / 'BRIEF.md').write_text(render_brief(task, mine))
    for group, ids in groups.items():
        write_group(REPO / '.local/tasks' / group, [REPO / '.local/tasks' / group / i for i in ids])
    if moved:
        (run / 'fpfast.json').write_text(json.dumps(moved, indent=2) + '\n')
    t_py = time.monotonic() - t0
    total = t_setup + t_ghidra + t_py
    timing = {'functions': len(rows), 'setup_s': round(t_setup, 1), 'ghidra_s': round(t_ghidra, 1),
              'python_s': round(t_py, 2), 'total_s': round(total, 1), 's_per_function': round(total / len(rows), 2)}
    (run / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    print(json.dumps(timing))


def refresh_pack(pack_dir, target, img, addrlib, comms):
    """Rewrite one pack's Drafter aids, trimmed excerpt and README from pack.json (no Ghidra run)."""
    pack_dir = Path(pack_dir)
    pack = json.loads((pack_dir / 'pack.json').read_text())
    if pack['image_sha256'] != target['image_sha256']:
        raise SystemExit(f'{pack_dir}: pack is for another image')
    ident = pack['identity']
    for key in ('instructions', 'cond_branches', 'indirect_calls', 'fp_arith'):
        pack.setdefault(key, None)  # packs from earlier exporter versions lack some counts
    listing = (pack_dir / 'listing.txt').read_text() if (pack_dir / 'listing.txt').is_file() else ''
    pack['fp_equality_without_parity'] = fp_equality_without_parity(listing)
    excerpt = None
    if ident.get('owning_class'):
        for c in comms:
            excerpt = c.class_excerpt(ident['owning_class'])
            if excerpt:
                break
    name = pack['files'].get('class_excerpt')
    if excerpt and name:
        method = (ident.get('community_name') or '').split('::')[-1]
        text, trimmed = trim_excerpt(excerpt['text'], {o for o, *_ in observed_offsets(listing)}, [method])
        (pack_dir / name).write_text(f'// {excerpt["origin"]}: {excerpt["path"]}:{excerpt["line"]}'
                                     + (' (trimmed to the declaration head, virtuals, this method and the members '
                                        'at observed offsets)' if trimmed else '') + '\n' + text + '\n')
    files, lines = drafter_aids(pack_dir, img, addrlib, comms, ident, listing, excerpt, target['build_id'])
    pack['files'].update(files)
    lines += table_aids(pack, img)
    (pack_dir / 'pack.json').write_text(json.dumps(pack, indent=2, default=hex) + '\n')
    (pack_dir / 'README.md').write_text(render_pack_readme(pack) + '\n'.join(lines))
    return pack, files


def refresh_briefs(task_dirs):
    """Rewrite only BRIEF.md (and a group's group.json and combined brief) from the task files and
    pack.json already on disk: no image, Ghidra or class-material run, and the attempt history
    (attempts.jsonl, attempts/) is never touched."""
    done = []
    for t in (Path(d) for d in task_dirs):
        if (t / 'group.json').is_file() and not (t / 'task.json').is_file():
            group = json.loads((t / 'group.json').read_text())
            units = [t / u['dir'] for u in group['units']]
            for u in units:
                done += refresh_briefs([u])
            write_group(t, units)
            done.append(t / 'BRIEF.md')
            continue
        task = json.loads((t / 'task.json').read_text())
        packs = [json.loads((REPO / f['pack'] / 'pack.json').read_text()) for f in task['functions'] if f.get('pack')]
        (t / 'BRIEF.md').write_text(render_brief(task, packs))
        done.append(t / 'BRIEF.md')
    return done


def cmd_refresh(args):
    """Rewrite the Drafter aids of existing packs; with --tasks also their class material and briefs."""
    if args.briefs_only:
        for b in refresh_briefs(args.tasks or []):
            print(f'wrote {b}')
        return
    cfg = load_config(args.config)
    target, img, addrlib, comms = setup(cfg)
    pack_dirs = list(args.pack)
    tasks = [Path(t) for t in args.tasks or []]
    for t in tasks:
        task = json.loads((t / 'task.json').read_text())
        pack_dirs += [REPO / f['pack'] for f in task['functions'] if f.get('pack')]
    if tasks:
        # Class material first, so the refreshed function READMEs can point at it.
        write_class_material(tasks, target, img, addrlib, comms)
    for d in dict.fromkeys(str(p) for p in pack_dirs):
        _, files = refresh_pack(d, target, img, addrlib, comms)
        print(f'{d}: ' + (', '.join(sorted(files)) or 'no aids'))
    for t in tasks:
        task = json.loads((t / 'task.json').read_text())
        packs = [json.loads((REPO / f['pack'] / 'pack.json').read_text()) for f in task['functions'] if f.get('pack')]
        (t / 'README.md').write_text(render_task_readme(task, packs))
        (t / 'BRIEF.md').write_text(render_brief(task, packs))


def named_rvas(img, addrlib, comms):
    """Function starts in executable sections that CommonLibSSE-NG names (not vtables or RTTI)."""
    out = set()
    by_id = {}
    for rva, ids in addrlib['by_rva'].items():
        for i in ids:
            by_id[i] = rva
    for ae, rows in comms[0].by_ae.items():
        rva = by_id.get(ae)
        if rva is None or not any(r['kind'] not in ('vtable', 'rtti', 'nirtti', 'data') for r in rows):
            continue
        sec = img.section(rva)
        if sec and sec.flags & 0x20000000:
            out.add(rva)
    return sorted(out)


def cmd_survey(args):
    cfg = load_config(args.config)
    target, img, addrlib, comms = setup(cfg)
    label = 'named' if args.named else f'n{args.sample}-s{args.seed}'
    run = REPO / '.local/packs/_survey' / f'{target["build_id"]}-{label}'
    run.mkdir(parents=True, exist_ok=True)
    if args.named:
        (run / 'rvas.txt').write_text(''.join('0x%x\n' % r for r in named_rvas(img, addrlib, comms)))
        selector = str(run / 'rvas.txt')
    else:
        selector = f'@random:{args.sample}:{args.seed}'
    t = run_ghidra(cfg, selector, run / 'ghidra', 'refs', run / 'ghidra.log')
    t0 = time.monotonic()
    gmeta, grefs = load_ghidra(run / 'ghidra')
    reasons, verdicts, rows = {}, {}, []
    for rva in sorted(gmeta):
        fact = classify(img, addrlib, comms, rva, gmeta[rva], grefs.get(rva, []))
        verdicts[fact['verdict']] = verdicts.get(fact['verdict'], 0) + 1
        for r in fact['reasons']:
            reasons[r] = reasons.get(r, 0) + 1
        ae = addrlib['by_rva'].get(rva, [])
        ident, _ = community_identity(comms, ae)
        g = gmeta[rva]
        res = {}
        for ref in fact.get('references', []):
            res[ref['resolution']] = res.get(ref['resolution'], 0) + 1
        rows.append('\t'.join(map(str, (
            hex(rva), fact.get('size'), fact['verdict'], ','.join(fact['reasons']) or '-',
            len(fact['cautions']), ','.join(map(str, ae)) or '-', g.get('n_instr'), g.get('fp_arith'),
            g.get('cond_branches'), json.dumps(fact.get('reference_counts', {}), sort_keys=True),
            json.dumps(res, sort_keys=True), fact.get('unwind_form', '-'),
            (short_name(ident['name']) + ' [' + ident['how'] + ', ' + ident['origin'].split(' ')[0] + ']')
            if ident else '-'))))
    header = 'rva\tsize\tverdict\treasons\tcautions\tae_ids\tninstr\tfp_arith\tcond_branches\trefs\tresolutions\tunwind\tname\n'
    (run / 'verdicts.tsv').write_text(header + '\n'.join(rows) + '\n')
    n = len(gmeta)
    summary = {'functions': n, 'selector': 'community-named' if args.named else f'random seed {args.seed}',
               'ghidra_s': round(t, 1), 'python_s': round(time.monotonic() - t0, 1),
               's_per_function': round((t + time.monotonic() - t0) / max(n, 1), 3),
               'verdicts': verdicts, 'reasons': dict(sorted(reasons.items(), key=lambda kv: -kv[1]))}
    (run / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--config', default=str(DEFAULT_CONFIG))
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('packs')
    a.add_argument('list')
    a.add_argument('--recipe', default=DEFAULT_RECIPE)
    a.add_argument('--max-attempts', type=int, default=12)
    a.add_argument('--attempts-per-function', type=int, default=None,
                   help='Budget = N x compared functions of the task (overrides --max-attempts)')
    a.add_argument('--fpfast', choices=('keep', 'unit', 'drop'), default='keep',
                   help='Functions with a float equality test lacking a parity branch: keep them under the '
                        'default recipe, move the whole task to --fpfast-recipe when its other functions are '
                        'recipe-neutral (else drop them), or drop them')
    a.add_argument('--fpfast-recipe', default='o2-fpfast')
    a.add_argument('--class-material', action='store_true',
                   help='Also write .local/packs/<build>/class/<Class>/ for the classes of these tasks')
    a.add_argument('--shared-classes-name', default='_shared-classes.json',
                   help='File name of the shared-class summary under class/ (a new name keeps an earlier batch\'s)')
    pl = sub.add_parser('plan', help='Propose class-grouped units from the community-named survey')
    pl.add_argument('--survey', default=None, help='Default: .local/packs/_survey/<build>-named')
    pl.add_argument('--label', default='plan')
    pl.add_argument('--classes', type=int, default=8)
    pl.add_argument('--per-class', type=int, default=5)
    pl.add_argument('--total', type=int, default=None, help='Grow short batches toward this many functions')
    pl.add_argument('--min-functions', type=int, default=4)
    pl.add_argument('--max-function-bytes', type=int, default=500)
    pl.add_argument('--max-unit-bytes', type=int, default=1200)
    pl.add_argument('--extend', default=None, help='The one class whose existing unit this batch extends')
    pl.add_argument('--area', action='append', help='CLASS=AREA for an owning-system area (rule 1)')
    pl.add_argument('--exclude', action='append', help='Class to leave out')
    pl.add_argument('--task-prefix', default='batch-')
    pl.add_argument('--reuse-evidence', action='append',
                    help='Inventory entries citing this findings/ file stay selectable (reproduce a recorded plan)')
    pl.add_argument('--order', choices=('survey', 'fanin', 'cheap'), default='survey',
                    help='fanin: plan from the whole-image table of build_function_table.py, high fan-in small '
                         'functions of classes that pass the per-class checks first; cheap: small and normal '
                         'tasks of functions expected to pass in few attempts (tools/ghidra/plan_cheap.py)')
    pl.add_argument('--parked', action='append',
                    help='cheap: census JSON whose "skip" and "m2_noh" RVA lists are parked families')
    pl.add_argument('--catalogue', default=None, help='cheap: FNV inline-helper catalogue (JSON keyed by class)')
    pl.add_argument('--normal-functions', type=int, default=None, help='cheap: functions reserved for normal tasks')
    pl.add_argument('--table', default=None, help='Default: .local/analysis')
    pl.add_argument('--eh', type=int, default=20, help='fanin: C++ EH functions with few states to mix in')
    pl.add_argument('--max-eh-states', type=int, default=3)
    pl.add_argument('--max-classes-per-area', type=int, default=8)
    pl.add_argument('--evidence', default='findings/fourth-batch-selection.md',
                    help='fanin: findings file the inventory rows cite')
    s = sub.add_parser('survey')
    s.add_argument('--sample', type=int, default=2000)
    s.add_argument('--seed', type=int, default=1)
    s.add_argument('--named', action='store_true', help='Every community-named function instead of a sample')
    r = sub.add_parser('refresh', help='Rebuild Drafter aids of existing packs without running Ghidra')
    r.add_argument('pack', nargs='*')
    r.add_argument('--tasks', nargs='+', help='Task dirs: refresh their packs, class material, README and BRIEF')
    r.add_argument('--briefs-only', action='store_true',
                   help='With --tasks (unit or group dirs): rewrite only the briefs from files on disk')
    b = sub.add_parser('bind')
    b.add_argument('--task', required=True)
    b.add_argument('--object', default=None, help='Default: the newest attempts/<NNN>/candidate.obj')
    args = p.parse_args()
    if args.cmd == 'packs':
        cmd_packs(args)
    elif args.cmd == 'survey':
        cmd_survey(args)
    elif args.cmd == 'refresh':
        cmd_refresh(args)
    elif args.cmd == 'plan':
        {'fanin': cmd_plan_table, 'cheap': cmd_plan_cheap}.get(args.order, cmd_plan)(args)
    else:
        sys.exit(bind(args.task, args.object))


if __name__ == '__main__':
    main()
