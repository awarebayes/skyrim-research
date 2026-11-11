"""Build private per-function context packs and Drafter task directories.

Usage (repository root; see tools/ghidra/README.md):

    python3 tools/ghidra/export_pack.py packs <list file>     # packs + task dirs
    python3 tools/ghidra/export_pack.py survey --sample 2000 --seed 1
    python3 tools/ghidra/export_pack.py bind --task .local/tasks/<id> --object <candidate.obj>

The list file has one function per line: `<build id> <rva> <task id> [<unit .cpp path>]`.
Machine-specific paths (Ghidra, project, image, community checkouts) come from a private config,
by default .local/config/export_pack.json. Everything this tool writes is game-derived and goes
under .local/ only; the tool itself contains no game data.
"""
import argparse
import bisect
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
from pecoff import CoffObject, PeImage  # noqa: E402
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
# Reasons that make comparator contract v1 refuse the function outright.
UNSUPPORTED = {'exception-handler', 'chained-unwind', 'unwind-version', 'multiple-pdata', 'pdata-not-at-entry',
               'addr64', 'jump-table', 'import-thunk', 'thunk', 'unresolvable-reference', 'split-body',
               'not-a-function'}


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


def load_ghidra(out_dir):
    meta, refs = {}, {}
    for line in (Path(out_dir) / 'meta.tsv').read_text().splitlines():
        rva, found, name, nsyms, ranges, ninstr, computed, ctargets, thunk, fp, cond, icalls = line.split('\t')
        meta[int(rva, 16)] = {
            'found': found == '1', 'ghidra_name': name,
            'ranges': [] if ranges == '-' else [tuple(int(x, 16) for x in r.split('-')) for r in ranges.split(',')],
            'n_instr': int(ninstr), 'computed_jumps': int(computed), 'computed_targets': int(ctargets),
            'thunk': thunk == '1', 'fp_arith': int(fp), 'cond_branches': int(cond),
            'indirect_calls': int(icalls)}
    for line in (Path(out_dir) / 'refs.tsv').read_text().splitlines():
        rva, off, rtype, target, mnem, opi, names, tentry = line.split('\t')
        refs.setdefault(int(rva, 16), []).append({
            'offset': int(off), 'ref_type': rtype, 'target': int(target, 16), 'mnemonic': mnem,
            'operand': int(opi), 'ghidra_names': names, 'target_entry': int(tentry)})
    return meta, refs


# ---------------------------------------------------------------------------------------------
# Suitability for comparator contract v1.

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
    """Return the pack facts for one function: range, unwind, references and a v1 verdict."""
    reasons, cautions = [], []
    if not gmeta or not gmeta['found']:
        return {'rva': rva, 'verdict': 'unsupported', 'reasons': ['not-a-function'], 'cautions': []}
    entry = img.pdata_at.get(rva)
    ranges = gmeta['ranges']
    body_lo = min(r[0] for r in ranges)
    body_hi = max(r[1] for r in ranges)
    if len(ranges) > 1:
        reasons.append('split-body')
    if entry:
        end, unwind_rva = entry
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
    hi = max(rva + size, body_hi)
    lo = min(rva, body_lo)
    entries = img.pdata_intersecting(lo, hi)
    if len(entries) > 1:
        reasons.append('multiple-pdata')
    if body_hi > rva + size and entry:
        cautions.append('analysis body extends %d bytes past the .pdata end' % (body_hi - rva - size))
    for b, e, u in entries:
        info = img.unwind(u)
        if info['version'] != 1:
            reasons.append('unwind-version')
        if info['flags'] & 4:
            reasons.append('chained-unwind')
        if info['flags'] & 3:
            reasons.append('exception-handler')
    if img.dir64_in(rva, rva + size):
        reasons.append('addr64')
    if gmeta['computed_targets'] >= 2:
        reasons.append('jump-table')
    elif gmeta['computed_jumps']:
        cautions.append('indirect jump without recovered targets (tail call through a register or memory, '
                        'or an unrecovered switch)')
    if gmeta['thunk']:
        reasons.append('thunk')
    refs, seen = [], set()
    for r in grefs:
        t = r['target']
        if rva <= t < rva + size:
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
    reasons = sorted(set(reasons))
    verdict = 'unsupported' if reasons else ('caution' if cautions else 'supported')
    counts = {}
    for ref in refs:
        counts[ref['kind']] = counts.get(ref['kind'], 0) + 1
    return {'rva': rva, 'size': size, 'verdict': verdict, 'reasons': reasons, 'cautions': sorted(set(cautions)),
            'pdata_entries': len(entries), 'unwind': unwind, 'unwind_form': unwind_form(unwind),
            'dir64_in_range': len(img.dir64_in(rva, rva + size)), 'ghidra': gmeta, 'references': refs,
            'reference_counts': counts}


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


def write_pack(pack_dir, fact, target, addrlib, comms, gdir, timing):
    pack_dir.mkdir(parents=True, exist_ok=True)
    rva = fact['rva']
    ae_ids = addrlib['by_rva'].get(rva, [])
    ident, comm = community_identity(comms, ae_ids)
    excerpt = source = None
    if ident:
        cls = owning_class(ident['name'])
        if cls:
            # NG first: its MIT licence lets type and field names be published with attribution.
            for c in comms:
                excerpt = c.class_excerpt(cls)
                if excerpt:
                    break
        source = comm.source_excerpt(ident['source'])
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
    if excerpt:
        name = 'class-excerpt.GPL-local-only.h' if gpl else 'class-excerpt.h'
        (pack_dir / name).write_text(f'// {excerpt["origin"]}: {excerpt["path"]}:{excerpt["line"]}\n'
                                     + excerpt['text'] + '\n')
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
        'verdict': fact['verdict'], 'reasons': fact['reasons'], 'cautions': fact['cautions'],
        'reference_counts': fact.get('reference_counts', {}), 'references': fact.get('references', []),
        'instructions': fact.get('ghidra', {}).get('n_instr'),
        'indirect_calls': fact.get('ghidra', {}).get('indirect_calls'),
        'fp_arith': fact.get('ghidra', {}).get('fp_arith'),
        'cond_branches': fact.get('ghidra', {}).get('cond_branches'),
        'files': files, 'timing_seconds': timing}
    (pack_dir / 'pack.json').write_text(json.dumps(pack, indent=2, default=hex) + '\n')
    (pack_dir / 'README.md').write_text(render_pack_readme(pack))
    return pack


def render_pack_readme(p):
    ident = p['identity']
    lines = [f'# PRIVATE context pack: {p["build_id"]} {p["rva_hex"]}', '',
             'Game-derived (listing, decompiler output, community excerpts). Local use only; never copy any',
             'part into a tracked file, issue, PR, log or upload.', '',
             f'- Size: {p["size"]} bytes (from .pdata unless a caution says otherwise); '
             f'{p["instructions"]} instructions; {p["cond_branches"]} conditional branches; '
             f'{p["indirect_calls"]} indirect calls (register or vtable unless listed below); {p["fp_arith"]} SSE arithmetic instructions.',
             f'- Community name: `{ident["community_name"]}` ({ident["name_origin"]}, unverified; '
             f'{ident["name_how"]}; {ident["name_source"]}).',
             f'- Address Library ids: {ident["ae_ids"] or "none"}. Ghidra label: `{ident["ghidra_name"]}`.',
             f'- Owning class: `{ident["owning_class"]}`; excerpt: `{p["files"].get("class_excerpt", "none")}`; '
             f'name use site: `{p["files"].get("source_excerpt", "none")}`.',
             f'- Unwind: {p["unwind_form"]}; .pdata entries touching the range: {p["pdata_entries"]}; '
             f'DIR64 relocations in range: {p["dir64_in_range"]}.',
             f'- Comparator v1 verdict: **{p["verdict"]}**' + (f' ({", ".join(p["reasons"])})' if p['reasons'] else '')
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
        lines.append(f'| 0x{r["from_offset"]:x} | {r["kind"]} {r["mnemonic"]} | 0x{r["target_rva"]:x} | '
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


def write_task(task_id, unit_cpp, recipe, packs, target, task_root, max_attempts):
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
    for rec in shared:
        # Compared on every attempt too, so an edit to the shared unit that breaks an accepted
        # function shows up at once instead of at integration.
        if rec['symbol'] and rec['rva'] not in {f['rva'] for f in functions}:
            functions.append({'rva': rec['rva'], 'size': rec['size'], 'symbol': rec['symbol'],
                              'function_id': rec['function_id'], 'community_name': rec['community_name'],
                              'name_origin': 'COMMUNITY', 'verdict': 'already ' + rec['status'],
                              'pack': None, 'role': 'regression'})
            symbols.setdefault(rec['symbol'], {'rva': int(rec['rva'], 16), 'size': rec['size']})
    task = {'task_id': task_id, 'build_id': target['build_id'], 'compiled': unit_cpp,
            'recipe': f'reconstruction/recipes/{recipe}.json', 'symbols': 'symbols.json',
            'functions': functions, 'max_attempts': max_attempts,
            'export': {'generator': 'tools/ghidra/export_pack.py', 'task_schema': TASK_SCHEMA,
                       'target_image_sha256': target['image_sha256'],
                       'unit_already_records': shared}}
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
              '3. `symbol` starts as `unbound:<community name>`. Run one attempt (it compiles; the comparator',
              '   fails the unbound function), then fill the symbols from the fetched object:', '',
              '   ```sh',
              f'   python3 tools/ghidra/export_pack.py bind --task .local/tasks/{task["task_id"]}',
              '   ```', '',
              '   It matches `?Method@Class@@...` definitions to the community names of the functions and',
              '   undefined symbols to the community names of the references, adds constants and imports, and',
              '   lists what it could not bind. Bind the rest by hand in `symbols.json` from the pack tables',
              '   (name -> RVA of the target), never by guessing.',
              '4. Re-run `tools/verifier/attempt .local/tasks/' + task['task_id'] + '` from your worktree after',
              '   binding, and bind again whenever you change a declaration. Exit 0 is review evidence only,',
              '   never `matched`.', '']
    return '\n'.join(lines)


# ---------------------------------------------------------------------------------------------
# bind: fill task symbols and reference symbols from a compiled object.

def demangle_simple(name):
    """Qualified name for plain `?name@scope@...@@` decorations; None for templates and operators."""
    m = re.match(r'\?\?([01])(\w+)@((?:\w+@)*)@', name)
    if m:
        scopes = [m.group(2)] + [x for x in m.group(3).split('@') if x]
        return '::'.join(reversed(scopes)) + '::' + ('~' if m.group(1) == '1' else '') + m.group(2)
    m = re.match(r'\?(\w+)@((?:\w+@)*)@', name)
    if not m:
        return None
    scopes = [x for x in m.group(2).split('@') if x]
    return '::'.join(list(reversed(scopes)) + [m.group(1)])


def bind(task_dir, obj_path=None):
    task_dir = Path(task_dir)
    if obj_path is None:
        # The attempt command fetches each compiled object into attempts/<NNN>/.
        objs = sorted(task_dir.glob('attempts/[0-9][0-9][0-9]/candidate.obj'))
        if not objs:
            raise SystemExit(f'no attempts/*/candidate.obj under {task_dir}; pass --object')
        obj_path = objs[-1]
        print(f'object: {obj_path}')
    task = json.loads((task_dir / 'task.json').read_text())
    smap = json.loads((task_dir / 'symbols.json').read_text())
    obj = CoffObject(Path(obj_path).read_bytes())
    defined, section_of = {}, {}
    for sym in obj.symbols.values():
        if sym.storage == 2 and sym.section > 0 and obj.section(sym.section).flags & 0x20 and sym.value == 0:
            defined[sym.name] = demangle_simple(sym.name)
            section_of[sym.name] = sym.section
    report = {'bound_functions': [], 'bound_references': [], 'unbound_references': [], 'unbound_functions': []}
    for f in task['functions']:
        hits = [n for n, q in defined.items() if q and f['community_name'] and q == f['community_name']]
        if len(hits) == 1 and (not f.get('symbol') or f['symbol'].startswith(UNBOUND) or f['symbol'] == hits[0]):
            f['symbol'] = hits[0]
            smap['symbols'][hits[0]] = {'rva': int(f['rva'], 16), 'size': f['size']}
            report['bound_functions'].append((f['rva'], hits[0]))
        elif not f.get('symbol') or f['symbol'].startswith(UNBOUND):
            report['unbound_functions'].append((f['rva'], f['community_name'], hits))
    by_name = {}
    for f in task['functions']:
        if not f.get('pack'):
            continue
        pack = json.loads((REPO / f['pack'] / 'pack.json').read_text())
        for r in pack['references']:
            for cn in r['community_names']:
                if cn['kind'] in ('vtable', 'rtti', 'nirtti'):
                    continue
                by_name.setdefault(short_name(cn['name']), set()).add(r['target_rva'])
    task_syms = {f['symbol'] for f in task['functions'] if f.get('symbol') and not f['symbol'].startswith(UNBOUND)}
    # Only relocations inside the compared functions need map entries; RTTI, destructors and
    # other helpers of the unit are never compared.
    needed = set()
    for name in task_syms:
        if name not in section_of:
            continue
        sec = obj.section(section_of[name])
        for rel in sec.relocs:
            target = obj.symbols[rel.symbol]
            if target.section != section_of[name]:
                needed.add(target.name)
    for name in sorted(needed):
        if name in smap['symbols'] or name in task_syms:
            continue
        q = demangle_simple(name)
        targets = by_name.get(q, set()) if q else set()
        if len(targets) == 1:
            smap['symbols'][name] = {'rva': next(iter(targets)), 'size': None}
            report['bound_references'].append((name, hex(next(iter(targets)))))
        else:
            report['unbound_references'].append(name)
    (task_dir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
    (task_dir / 'symbols.json').write_text(json.dumps(smap, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if not (report['unbound_functions'] or report['unbound_references']) else 1


# ---------------------------------------------------------------------------------------------

def cmd_packs(args):
    cfg = load_config(args.config)
    t_setup = time.monotonic()
    target, img, addrlib, comms = setup(cfg)
    t_setup = time.monotonic() - t_setup
    rows = []
    for line in Path(args.list).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        build, rva, task_id = parts[0], int(parts[1], 0), parts[2]
        if build != target['build_id']:
            raise SystemExit(f'{build}: only the pinned build {target["build_id"]} has packs; '
                             'addresses never transfer between builds')
        rows.append((rva, task_id, parts[3] if len(parts) > 3 else None))
    run = REPO / '.local/packs/_runs' / time.strftime('%Y%m%dT%H%M%S')
    run.mkdir(parents=True, exist_ok=True)
    (run / 'rvas.txt').write_text(''.join('0x%x\n' % r for r, _, _ in rows))
    t_ghidra = run_ghidra(cfg, str(run / 'rvas.txt'), run / 'ghidra', 'full', run / 'ghidra.log')
    gmeta, grefs = load_ghidra(run / 'ghidra')
    t0 = time.monotonic()
    packs, by_task = {}, {}
    for rva, task_id, unit in rows:
        fact = classify(img, addrlib, comms, rva, gmeta.get(rva), grefs.get(rva, []))
        pack = write_pack(REPO / '.local/packs' / target['build_id'] / hex(rva), fact, target, addrlib, comms,
                          run / 'ghidra', {'ghidra_share': round(t_ghidra / len(rows), 2)})
        packs[rva] = pack
        by_task.setdefault(task_id, []).append((pack, unit))
        print(f'{hex(rva)} {pack["size"]} B {pack["verdict"]} {",".join(pack["reasons"])} '
              f'{pack["identity"]["community_name"]}')
    for task_id, items in by_task.items():
        units = {u for _, u in items if u}
        if len(units) > 1:
            raise SystemExit(f'task {task_id}: one task is one unit, got {sorted(units)}')
        cls = items[0][0]['identity']['owning_class'] or 'Unknown'
        existing = sorted((REPO / 'reconstruction').glob(f'*/{cls}.cpp'))
        # A class already reconstructed keeps its unit: one pair per class (reconstruction/README.md).
        unit = units.pop() if units else (existing[0].relative_to(REPO).as_posix() if existing
                                          else f'reconstruction/misc/{cls}.cpp')
        write_task(task_id, unit, args.recipe, [p for p, _ in items], target, REPO / '.local/tasks',
                   args.max_attempts)
    t_py = time.monotonic() - t0
    total = t_setup + t_ghidra + t_py
    timing = {'functions': len(rows), 'setup_s': round(t_setup, 1), 'ghidra_s': round(t_ghidra, 1),
              'python_s': round(t_py, 2), 'total_s': round(total, 1), 's_per_function': round(total / len(rows), 2)}
    (run / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    print(json.dumps(timing))


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
    s = sub.add_parser('survey')
    s.add_argument('--sample', type=int, default=2000)
    s.add_argument('--seed', type=int, default=1)
    s.add_argument('--named', action='store_true', help='Every community-named function instead of a sample')
    b = sub.add_parser('bind')
    b.add_argument('--task', required=True)
    b.add_argument('--object', default=None, help='Default: the newest attempts/<NNN>/candidate.obj')
    args = p.parse_args()
    if args.cmd == 'packs':
        cmd_packs(args)
    elif args.cmd == 'survey':
        cmd_survey(args)
    else:
        sys.exit(bind(args.task, args.object))


if __name__ == '__main__':
    main()
