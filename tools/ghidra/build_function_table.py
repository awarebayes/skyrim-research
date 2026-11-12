"""Whole-image function and class tables for planning, class skeletons and packs.

    python3 tools/ghidra/build_function_table.py [--config .local/config/export_pack.json]
            [--ghidra-dir DIR] [--rerun-ghidra] [--rerun-disasm] [--out .local/analysis]

Writes, all private (game-derived) under `.local/analysis/`:

- `functions.jsonl`: one row per Ghidra function entry: rva, size, kind (ordinary, eh-funclet,
  static-initializer, teardown, thunk, import-thunk), POGO group, owning class and how it is known,
  names from each approved source with the source tagged, unwind/EH facts, callers and callees,
  L1/L2 cluster keys, and the comparator v2 verdict the exporter's own `classify` gives.
- `classes.jsonl`: one row per class with a primary vftable: bases, slot targets, object size from
  the deleting destructor, the community join with the per-class checks C1 to C4 of
  docs/resource-guidelines.md, and the slot names each source contributes where its checks pass.
- `callsites.json`: per callee, what direct callers set up before the call (P5 evidence).
- `table-meta.json`: inputs, their hashes and the time each stage took.

Inputs: one headless Ghidra run over every function (`ExportPack.java @all refs`, about 35 s,
cached under `.local/analysis/cache/`), one llvm-objdump pass over the image (cached), the image's
own .pdata, unwind, EH, RTTI, POGO and relocation data, the Address Library, the community
checkouts and meh321's name list from the private config. Original code; no game data in it.
"""
import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import pickle
import re
import shutil
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import export_pack as ep  # noqa: E402

TABLE_SCHEMA = 1
DISASM_SCHEMA = 2
OBJDUMP_CANDIDATES = ('llvm-objdump', '/opt/homebrew/opt/llvm/bin/llvm-objdump', '/usr/local/opt/llvm/bin/llvm-objdump')
FUNCLET_PREFIXES = ('Unwind@', 'Catch@', 'Catch_All@')
CXX_HANDLERS = ('__CxxFrameHandler3', '__GSHandlerCheck_EH')

# Source tags. Labels are the `Labels: v2` forms of docs/drafter-card.md.
SOURCES = ('ng-id', 'po3-id', 'ng-slot', 'po3-slot', 'meh321')


def community_label(source, cfg):
    if source.startswith('ng'):
        return f'COMMUNITY(CharmedBaryon/CommonLibSSE-NG@{cfg["ng_revision"][:7]}, MIT)'
    if source.startswith('po3'):
        return f'COMMUNITY(powerof3/CommonLibSSE@{cfg["po3_revision"][:7]}, GPL-3.0)'
    if source == 'meh321':
        return f'COMMUNITY(meh321/AddressLibrary@{cfg.get("meh321_revision", "0000000")[:12]}, permission)'
    return 'GUESS'


# ---------------------------------------------------------------------------------------------
# Disassembly pass: cluster keys, direct call graph, call-site census.

RIP_COMMENT = re.compile(r'\[rip [+-] 0x[0-9a-f]+\]')
NUM = re.compile(r'0x[0-9a-f]+|\b\d+\b')
BRANCH_TARGET = re.compile(r'^0x([0-9a-f]+)')
NO_DEST = {'cmp', 'test', 'push', 'call', 'jmp', 'ucomiss', 'comiss', 'ucomisd', 'comisd', 'bt', 'ret', 'nop',
           'prefetcht0', 'prefetcht1', 'prefetchnta', 'ptest'}
INT_ARGS = {}
for _slot, (_q, _d, _w, _b) in enumerate((('rcx', 'ecx', 'cx', 'cl'), ('rdx', 'edx', 'dx', 'dl'),
                                          ('r8', 'r8d', 'r8w', 'r8b'), ('r9', 'r9d', 'r9w', 'r9b'))):
    INT_ARGS.update({_q: (_slot, 'i8'), _d: (_slot, 'i4'), _w: (_slot, 'i2'), _b: (_slot, 'i1')})
XMM_ARGS = {'xmm%d' % i: i for i in range(4)}
STACK_ARG = re.compile(r'^(byte|word|dword|qword|xmmword) ptr \[rsp \+ 0x([0-9a-f]+)\]$')
PTR_WIDTH = {'byte': 'i1', 'word': 'i2', 'dword': 'i4', 'qword': 'i8', 'xmmword': 'x16'}
RET_REG = re.compile(r'\b(rax|eax|ax|al|xmm0)\b')
RET_WIDTH = {'rax': 'i8', 'eax': 'i4', 'ax': 'i2', 'al': 'i1', 'xmm0': 'f'}
WINDOW = 24


def xmm_width(mnemonic):
    m = mnemonic.lower()
    if m.endswith('ss') or m.endswith('ss2') or m.startswith('cvtsi2ss') or m == 'movd':
        return 'f4'
    if m.endswith('sd') or m.startswith('cvtsi2sd') or m == 'movq':
        return 'f8'
    return 'x16'


def setup_of(window):
    """{argument slot: width} written by the instructions since the last control transfer.

    Slots 0 to 3 are RCX/RDX/R8/R9 or XMM0 to XMM3 (MSVC x64 assigns by position), 4 and up the stack
    slots at [rsp+0x20+8k]. A register already holding the value (passed through unchanged) is not
    visible here, so this undercounts; callers read it as evidence, never as a signature."""
    out = {}
    for mn, ops in window:
        if mn in NO_DEST or not ops:
            continue
        dest = ops[0]
        if dest in INT_ARGS:
            slot, width = INT_ARGS[dest]
            out[slot] = 'p8' if mn == 'lea' else width
        elif dest in XMM_ARGS:
            out[XMM_ARGS[dest]] = xmm_width(mn)
        else:
            m = STACK_ARG.match(dest)
            if m and int(m.group(2), 16) >= 0x20 and int(m.group(2), 16) % 8 == 0 and mn.startswith('mov'):
                out[4 + (int(m.group(2), 16) - 0x20) // 8] = PTR_WIDTH[m.group(1)]
    # A store far above the argument area is a local of the caller; keep stack slots only while
    # they run on from slot 4 without a gap.
    k = 4
    while k in out:
        k += 1
    return {s: w for s, w in out.items() if s < 4 or s < k}


def edx_immediate(window):
    for mn, ops in reversed(window):
        if mn in NO_DEST or not ops:
            continue
        if ops[0] in ('edx', 'rdx', 'dx', 'dl'):
            if mn == 'mov' and len(ops) == 2 and re.fullmatch(r'0x[0-9a-f]+|\d+', ops[1]):
                return int(ops[1], 0)
            return None
    return None


def result_use(after):
    """How the instructions after a call treat RAX/XMM0: 'i8'...'f' read, 'overwritten', or 'none'."""
    for mn, ops in after:
        if mn in ('xor', 'sub', 'xorps', 'pxor') and len(ops) == 2 and ops[0] == ops[1]:
            if RET_REG.fullmatch(ops[0]):
                return 'overwritten'
            continue
        reads = ops if mn in NO_DEST else ops[1:]
        dest_mem = ops[0] if ops and '[' in ops[0] else ''
        for tok in list(reads) + [dest_mem]:
            m = RET_REG.search(tok)
            if m:
                return RET_WIDTH[m.group(1)]
        if ops and mn not in NO_DEST and RET_REG.fullmatch(ops[0]):
            return 'overwritten'
        if mn.startswith('j') or mn in ('call', 'ret'):
            break
    return 'none'


def split_ops(text):
    text = text.split('#', 1)[0].strip()
    if not text:
        return []
    out, depth, cur = [], 0, ''
    for ch in text:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    out.append(cur.strip())
    return out


class DisasmPass:
    """Streaming consumer of `llvm-objdump -d --no-show-raw-insn --x86-asm-syntax=intel` lines.

    `functions`: {entry rva: [(lo, hi), ...]} body ranges. Instructions are attributed to the
    range that holds them. L1 hashes each instruction as mnemonic plus operands with RIP-relative
    operands masked and branch targets rewritten (inside: offset from the entry; outside: EXT), so
    two functions share an L1 key when they differ only in relocated fields; L2 also masks every
    number (immediates and displacements)."""

    def __init__(self, functions, base, entries=None):
        self.base = base
        spans = sorted((lo, hi, rva) for rva, rs in functions.items() for lo, hi in rs if hi > lo)
        self.los = [s[0] for s in spans]
        self.his = [s[1] for s in spans]
        self.owner = [s[2] for s in spans]
        self.maxhi = {}
        for lo, hi, rva in spans:
            self.maxhi[rva] = max(self.maxhi.get(rva, 0), hi)
        self.entries = set(entries if entries is not None else functions)
        self.h1, self.h2 = {}, {}
        self.n_instr = Counter()
        self.callees = defaultdict(set)
        self.tail_callees = defaultdict(set)
        self.import_calls = defaultdict(set)
        self.first = {}
        self.edx_calls = defaultdict(list)
        self.census = {}
        self.window = []
        self.after = None
        self.cur = None
        self.keys = {}

    def _owner(self, rva):
        i = bisect.bisect_right(self.los, rva) - 1
        if i >= 0 and rva < self.his[i]:
            return self.owner[i]
        return None

    def _site(self, caller, callee, kind):
        setup = setup_of(self.window)
        imm = edx_immediate(self.window)
        if imm is not None:
            self.edx_calls[caller].append((callee, imm, kind))
        if kind != 'call':
            return
        c = self.census.get(callee)
        if c is None:
            c = self.census[callee] = {'sites': 0, 'arity': Counter(), 'slots': defaultdict(Counter),
                                       'result': Counter(), 'callers': set()}
        c['sites'] += 1
        c['callers'].add(caller)
        c['arity'][max(setup) + 1 if setup else 0] += 1
        for slot, width in setup.items():
            c['slots'][slot][width] += 1
        self.after = (callee, [])

    def _finish_after(self):
        if self.after:
            callee, rows = self.after
            self.census[callee]['result'][result_use(rows)] += 1
            self.after = None

    def instruction(self, addr, mn, ops, comment_target=None):
        rva = addr - self.base
        f = self._owner(rva)
        if f != self.cur:
            self._finish_after()
            self.window = []
            if self.cur is not None and self.cur in self.h1 and rva >= self.maxhi.get(self.cur, 0):
                self.keys[self.cur] = (self.h1.pop(self.cur).hexdigest(), self.h2.pop(self.cur).hexdigest())
            self.cur = f
        if f is None or mn == 'int3':
            return
        if f not in self.h1:
            if f in self.keys:  # a later range of a split body: keep its key from the first range
                return
            self.h1[f] = hashlib.blake2b(digest_size=10)
            self.h2[f] = hashlib.blake2b(digest_size=10)
        self.n_instr[f] += 1
        if f not in self.first:
            self.first[f] = (mn, ops, comment_target)
        text = ', '.join(ops)
        if RIP_COMMENT.search(text):
            text = RIP_COMMENT.sub('[rip+R]', text)
            if mn in ('call', 'jmp') and comment_target is not None:
                self.import_calls[f].add(comment_target - self.base)
        elif (mn.startswith('j') or mn == 'call' or mn.startswith('loop')) and ops:
            m = BRANCH_TARGET.match(ops[0])
            if m:
                t = int(m.group(1), 16) - self.base
                inside = self._owner(t) == f and mn != 'call'
                text = 'L%d' % (t - f) if inside else 'EXT'
                if not inside and t in self.entries and t != f:
                    if mn == 'call':
                        self.callees[f].add(t)
                        self._finish_after()
                        self._site(f, t, 'call')
                        self.window = []
                        line = mn + ' ' + text + '\n'
                        self.h1[f].update(line.encode())
                        self.h2[f].update(NUM.sub('#', line).encode())
                        return
                    if mn == 'jmp':
                        self.tail_callees[f].add(t)
                        self._site(f, t, 'jmp')
        line = mn + ' ' + text + '\n'
        self.h1[f].update(line.encode())
        self.h2[f].update(NUM.sub('#', line).encode())
        if self.after is not None:
            self.after[1].append((mn, ops))
            if len(self.after[1]) >= 4 or mn.startswith('j') or mn in ('call', 'ret'):
                self._finish_after()
        if mn.startswith('j') or mn in ('call', 'ret'):
            self.window = []
        else:
            self.window.append((mn, ops))
            if len(self.window) > WINDOW:
                self.window.pop(0)

    def feed(self, lines):
        for line in lines:
            colon = line.find(':')
            if colon < 8 or colon > 17 or line[0] == ' ':
                continue
            try:
                addr = int(line[:colon], 16)
            except ValueError:
                continue
            rest = line[colon + 1:].strip()
            if not rest:
                continue
            parts = rest.split('\t', 1)
            mn = parts[0].strip()
            if ' ' in mn:  # prefixes such as `lock` or `rep` stay part of the mnemonic
                mn = ' '.join(mn.split())
            opstext = parts[1] if len(parts) > 1 else ''
            target = None
            if '#' in opstext:
                m = re.search(r'#\s*0x([0-9a-f]+)', opstext)
                if m:
                    target = int(m.group(1), 16)
            self.instruction(addr, mn, split_ops(opstext), target)
        return self.finish()

    def finish(self):
        self._finish_after()
        for f in list(self.h1):
            self.keys[f] = (self.h1.pop(f).hexdigest(), self.h2.pop(f).hexdigest())
        census = {}
        for callee, c in self.census.items():
            census[callee] = {'sites': c['sites'], 'callers': len(c['callers']),
                              'arity': dict(sorted(c['arity'].items())),
                              'slots': {k: dict(v) for k, v in sorted(c['slots'].items())},
                              'result': dict(c['result'])}
        return {'schema': DISASM_SCHEMA, 'keys': self.keys, 'n_instr': dict(self.n_instr),
                'callees': {k: sorted(v) for k, v in self.callees.items()},
                'tail_callees': {k: sorted(v) for k, v in self.tail_callees.items()},
                'import_calls': {k: sorted(v) for k, v in self.import_calls.items()},
                'first': self.first, 'edx_calls': dict(self.edx_calls), 'census': census}


def find_objdump(cfg):
    for c in ([cfg.get('objdump')] if cfg.get('objdump') else []) + list(OBJDUMP_CANDIDATES):
        p = shutil.which(c) or (c if Path(c).is_file() else None)
        if p:
            return p
    raise SystemExit('llvm-objdump not found; set "objdump" in the private config')


def run_disasm(cfg, functions, base, entries, cache):
    if cache.is_file():
        data = pickle.loads(cache.read_bytes())
        if data.get('schema') == DISASM_SCHEMA:
            return data
    proc = subprocess.Popen([find_objdump(cfg), '-d', '--no-show-raw-insn', '--x86-asm-syntax=intel', cfg['image']],
                            stdout=subprocess.PIPE, text=True, bufsize=1 << 20)
    data = DisasmPass(functions, base, entries).feed(proc.stdout)
    if proc.wait() != 0:
        raise SystemExit('llvm-objdump failed')
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(data))
    return data


# ---------------------------------------------------------------------------------------------
# Image structure: POGO groups, RTTI vftables, EH outlines.

def pogo_groups(img):
    """[(rva, size, name)] from the POGO debug record: which .text$xx group each range came from."""
    rva, size = img.dirs[6]
    out = []
    if not size:
        return out
    for i in range(size // 28):
        typ, dsize, drva, draw = struct.unpack('<4I', img.read(rva + 28 * i + 12, 16))
        if typ != 13:
            continue
        blob = img.read(drva, dsize)
        p = 4
        while p + 8 < len(blob):
            r, s = struct.unpack_from('<II', blob, p)
            e = blob.index(b'\0', p + 8)
            out.append((r, s, blob[p + 8:e].decode('ascii', 'replace')))
            p = (e + 4) & ~3
    return sorted(out)


def demangle_type(raw):
    """Readable class name from a TypeDescriptor name (`.?AVInner@Outer@@` -> `Outer::Inner`).

    Templates keep their family name and the decorated arguments in angle brackets so every
    instantiation stays distinct; anonymous namespaces are shown as `(anonymous)`."""
    m = re.fullmatch(r'\.\?A[VU](.+)@@', raw)
    if not m:
        return raw
    body = m.group(1)
    if body.startswith('?$'):
        fam, _, args = body[2:].partition('@')
        return f'{fam}<{args}>'
    parts = []
    for p in body.split('@'):
        if not p:
            continue
        if p.startswith('?$'):
            parts.append(p[2:] + '<>')
        elif p.startswith('?A'):
            parts.append('(anonymous)')
        else:
            parts.append(p)
    return '::'.join(reversed(parts))


def ng_style(raw):
    """The `Outer__Inner` spelling CommonLibSSE uses in VTABLE_ ids, or None for templates."""
    m = re.fullmatch(r'\.\?A[VU](.+)@@', raw)
    if not m or '?$' in raw:
        return None
    parts = [p for p in m.group(1).split('@') if p and not p.startswith('?')]
    return '__'.join(reversed(parts))


def leaf(name):
    return re.sub(r'<.*', '', name or '').split('::')[-1].split('__')[-1]


class Rtti:
    """Vftables found from the image's CompleteObjectLocators and relocations alone."""

    def __init__(self, img, is_function):
        self.img = img
        self.base = ep.image_base(img)
        dir64 = img.dir64
        self.reloc = set(dir64)
        rdata = [s for s in img.pe.sections if not s.flags & ep.EXEC]
        cols = {}
        for pos in dir64:
            try:
                (va,) = struct.unpack('<Q', img.read(pos, 8))
            except Exception:
                continue
            t = va - self.base
            if t in cols:
                continue
            try:
                sig, off, cdoff, td, chd, selfr = struct.unpack('<6I', img.read(t, 24))
            except Exception:
                continue
            if sig == 1 and selfr == t and any(s.vaddr <= t < s.vaddr + s.vsize for s in rdata):
                cols[t] = (off, td, chd)
        self.vftables = {}
        colptr = set()
        for pos in dir64:
            try:
                (va,) = struct.unpack('<Q', img.read(pos, 8))
            except Exception:
                continue
            if va - self.base in cols:
                colptr.add(pos)
                self.vftables[pos + 8] = cols[va - self.base]
        self.slots = {}
        for vt in self.vftables:
            out, k = [], 0
            while True:
                p = vt + 8 * k
                if p not in self.reloc or (k and p in colptr):
                    break
                (va,) = struct.unpack('<Q', img.read(p, 8))
                t = va - self.base
                sec = img.section(t) if 0 < t < img.size_of_image else None
                if not sec or not sec.flags & ep.EXEC or not is_function(t):
                    break
                out.append(t)
                k += 1
            self.slots[vt] = out
        self._td = {}

    def td_name(self, td):
        if td not in self._td:
            sec = self.img.section(td + 16)
            start = sec.raw_ptr + td + 16 - sec.vaddr
            end = self.img.blob.index(b'\0', start)
            self._td[td] = self.img.blob[start:end].decode('ascii', 'replace')
        return self._td[td]

    def chain(self, chd):
        """Primary base chain (most derived first) and every base of the hierarchy descriptor."""
        _, _, count, bca = struct.unpack('<4I', self.img.read(chd, 16))
        allb, nested = [], []
        for i in range(min(count, 64)):
            (bcd,) = struct.unpack('<I', self.img.read(bca + 4 * i, 4))
            td, ncont = struct.unpack('<II', self.img.read(bcd, 8))
            allb.append(self.td_name(td))
            nested.append(ncont)
        chain = []
        for i, name in enumerate(allb):
            chain.append(name)
            if nested[i] == 0:
                break
        return chain, allb


def eh_outline(img, rva, unwind_rva, handler_name):
    """C++ EH object-lifetime facts from the FuncInfo of one function, or None.

    The unwind map is a tree of states (each entry: the state it unwinds to and the funclet that
    destroys what the state owns); the IP-to-state map says which code offsets run in which
    state. Together they show which objects have destructors and where each one is alive."""
    if handler_name not in CXX_HANDLERS:
        return None
    flags, length = ep.unwind_header(img.read(unwind_rva, 4), 'unwind info')
    (fi,) = struct.unpack('<I', img.read(unwind_rva + length + 4, 4))
    vals = struct.unpack('<10I', img.read(fi, 40))
    magic, max_state, umap, ntry, tmap, nip, ipmap = vals[:7]
    if not ep.FUNCINFO_MAGIC - 2 <= magic <= ep.FUNCINFO_MAGIC or max_state > 4096 or nip > 65536 or ntry > 1024:
        return {'magic': magic, 'states': None}
    states = []
    for i in range(max_state):
        to_state, action = struct.unpack('<iI', img.read(umap + 8 * i, 8))
        states.append({'state': i, 'to_state': to_state, 'action': action or None})
    ips = [struct.unpack('<Ii', img.read(ipmap + 8 * i, 8)) for i in range(nip)]
    tries = []
    for i in range(ntry):
        lo, hi, chigh, ncatch, harr = struct.unpack('<iiiII', img.read(tmap + 20 * i, 20))
        handlers = []
        for k in range(min(ncatch, 64)):
            adj, td, cobj, hrva, frame = struct.unpack('<IIiII', img.read(harr + 20 * k, 20))
            handlers.append({'type_descriptor': td or None, 'handler': hrva or None})
        tries.append({'try_low': lo, 'try_high': hi, 'catch_high': chigh, 'catches': handlers})
    return {'magic': magic, 'states': states, 'ip_to_state': [(ip, st) for ip, st in ips], 'try_blocks': tries}


# ---------------------------------------------------------------------------------------------
# Community class declarations: virtual slot comments, bases, asserted sizes.

CLASS_HEAD = re.compile(r'^\s*(?:template\s*<[^>]*>\s*)?(class|struct)\s+(?:alignas\([^)]*\)\s+)?(?:\w+_API\s+)?'
                        r'(\w+)\b(?!\s*;)')
SLOT_COMMENT = re.compile(r'^\s*([0-9A-Fa-f]{2,3})\b')
SECTION = re.compile(r'^\s*//\s*(override|add)\b\s*(?:\((.+)\))?\s*$')
SIZE_ASSERT = re.compile(r'static_assert\s*\(\s*sizeof\s*\(\s*([\w:<>, ]+?)\s*\)\s*==\s*(0x[0-9A-Fa-f]+|\d+)\s*\)')


def parse_class_bodies(text):
    """[{'name', 'vtable', 'bases', 'slots': [(slot, method, is_override, section)], 'line'}] for every
    class body in one header; nested bodies are their own entries and are not mixed into the outer one."""
    lines = text.splitlines()
    out = []
    for n, line in enumerate(lines):
        m = CLASS_HEAD.match(line)
        if not m or line.rstrip().endswith(';'):
            continue
        head, depth, opened, body_start = [], 0, False, None
        k = n
        while k < len(lines) and k < n + 40 and not opened:
            code = lines[k].split('//', 1)[0]
            if '{' in code:
                head.append(code.split('{', 1)[0])
                opened, body_start = True, k
                break
            if ';' in code:
                break
            head.append(code)
            k += 1
        if not opened:
            continue
        head_text = ' '.join(head)
        bases = []
        if ':' in head_text.replace('::', ''):
            after = re.split(r'(?<!:):(?!:)', head_text, maxsplit=1)[1]
            level, cur = 0, ''
            for ch in after:
                level += (ch == '<') - (ch == '>')
                if ch == ',' and level == 0:
                    bases.append(cur)
                    cur = ''
                else:
                    cur += ch
            bases.append(cur)
            bases = [re.sub(r'\b(public|protected|private|virtual)\b', '', b).strip() for b in bases if b.strip()]
        entry = {'name': m.group(2), 'vtable': None, 'bases': bases, 'slots': [], 'line': n + 1}
        section = None
        depth = 0
        for k in range(body_start, len(lines)):
            raw = lines[k]
            code, _, comment = raw.partition('//')
            if depth == 1:
                sm = SECTION.match(raw)
                if sm and not code.strip():
                    section = (sm.group(1), (sm.group(2) or '').strip() or None)
                mv = re.search(r'VTABLE\s*=\s*VTABLE_(\w+)', code)
                if mv and entry['vtable'] is None:
                    entry['vtable'] = mv.group(1)
                if ('virtual' in code or 'override' in code) and '(' in code:
                    cm = SLOT_COMMENT.match(comment)
                    nm = re.search(r'(~?\w+)\s*\(', code)
                    if cm and nm:
                        entry['slots'].append((int(cm.group(1), 16), nm.group(1),
                                               bool(re.search(r'\boverride\b', code)), section,
                                               ' '.join(code.split())))
            depth += code.count('{') - code.count('}')
            if depth <= 0:
                break
        out.append(entry)
    return out


def scan_community(root, cache=None):
    """{class key: entry} for one checkout; key is the VTABLE_ spelling when the body names one, else
    the class name. Also {class name: [asserted sizes]}. Cached per checkout revision."""
    if cache and cache.is_file():
        data = json.loads(cache.read_text())
        return data['classes'], data['sizes']
    classes, sizes = {}, defaultdict(list)
    for p in sorted((Path(root) / 'include').rglob('*.h')):
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = str(p.relative_to(root))
        for m in SIZE_ASSERT.finditer(text):
            sizes[m.group(1).strip()].append(int(m.group(2), 0))
        for e in parse_class_bodies(text):
            e['path'] = rel
            key = e['vtable'] or e['name']
            prev = classes.get(key)
            # A forward-declared helper with the same short name must not shadow the real body.
            if prev is None or (not prev['slots'] and e['slots']) or (prev['vtable'] is None and e['vtable']):
                classes[key] = e
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({'classes': classes, 'sizes': sizes}))
    return classes, dict(sizes)


def primary_slots(entry, chain_leaves, inherited_destructors=()):
    """{slot: (method, is_override)} of the primary vftable: slots in an `override (X)` section of a
    secondary base are numbered in that base's own vftable and are left out."""
    out = {}
    for slot, method, ov, section, *decl in entry['slots']:
        if section and section[0] == 'override' and section[1] and leaf(section[1]) not in chain_leaves:
            continue
        # A virtual destructor overrides an inherited virtual destructor even without the
        # optional `override` keyword. Only slots named by a checked ancestor count as evidence.
        implicit = method.startswith('~') and slot in inherited_destructors
        out.setdefault(slot, (method, ov or implicit, decl[0] if decl else None))
    return out


def class_checks(decl, own, parent, asserted, image_size, rtti_match, header_base, rtti_parent):
    """Per-class checks of docs/resource-guidelines.md, section 2, for one community source.

    decl: {slot: (method, is_override)}; own/parent: slot target lists from the image (parent None
    for a root class). Returns the outcome of each check and the slots whose names are usable."""
    r = {'declared_slots': len(decl)}
    if not decl:
        r['status'] = 'no slot comments'
    top = max(decl) + 1 if decl else 0
    r['C1_length'] = top <= len(own)
    deviations = []
    if parent is None:
        r['C2_range'] = None
        r['C3_pattern'] = None
    else:
        np_ = len(parent)
        bad = [k for k, (_, ov, *_) in decl.items() if (ov and k >= np_) or (not ov and k < np_)]
        r['C2_range'] = not bad
        r['C2_bad_slots'] = len(bad)
        checked = min(np_, len(own))
        for k in range(checked):
            if k in decl:
                if decl[k][1] and own[k] == parent[k]:
                    deviations.append(k)
            elif own[k] != parent[k]:
                deviations.append(k)
        r['C3_deviations'] = len(deviations)
        if not decl:
            r['C3_pattern'] = None
        elif not deviations:
            r['C3_pattern'] = 'pass'
        elif len(deviations) <= max(2, checked // 10):
            r['C3_pattern'] = 'soft'
        else:
            r['C3_pattern'] = 'fail'
    if not asserted or image_size is None:
        r['C4_size'] = None
    else:
        r['C4_size'] = image_size in asserted
    r['asserted_sizes'] = sorted(set(asserted or []))
    r['rtti_name'] = rtti_match
    hb, rp = leaf(header_base) if header_base else None, leaf(rtti_parent) if rtti_parent else None
    r['base_chain'] = (hb == rp) if (hb or rp) else True
    r['passes'] = bool(decl) and r['C1_length'] and r['C2_range'] is not False and \
        r['C3_pattern'] in ('pass', 'soft', None) and r['C4_size'] is not False and \
        rtti_match is not False and r['base_chain']
    r['usable_slots'] = sorted(k for k in decl if k < len(own) and k not in deviations) if r['passes'] else []
    return r


# ---------------------------------------------------------------------------------------------
# Areas (reconstruction/README.md rule: owning system, then prefix).

AREA_LABELS = {
    'netimmerse': 'NetImmerse (Ni*)', 'bsengine': 'Bethesda engine (BS*)', 'forms': 'Forms (TES*, BGS*)',
    'actors': 'Actors', 'magic': 'Magic', 'havok': 'Havok (hk*)', 'scaleform': 'Scaleform (GFx)',
    'bnet': 'Bethesda.net client', 'std': 'std and CRT', 'other': 'Other engine classes',
    'unattributed': 'No class known'}
MAGIC = re.compile(r'^(Magic|ActiveEffect|SpellItem|EnchantmentItem|ScrollItem|AlchemyItem|IngredientItem|'
                   r'MagicItem|MagicCaster|MagicTarget|ActorMagicCaster)')


def template_namespace(raw):
    """Namespace of a template instantiation from its decorated name (`?$Foo@H@BSScript@@` ->
    BSScript), or None. Short tails are argument codes, not namespaces."""
    m = re.search(r'@([A-Za-z_]\w{2,})@@$', raw or '')
    if not m or '?$' not in raw:
        return None
    ns = m.group(1)
    if ns in ('std', 'bnet', 'Concurrency', 'Scaleform') or re.match(r'(BS|Ni|hk)[A-Z]', ns):
        return ns
    return None


def area_of(name, ancestors=(), raw=None):
    n = name or ''
    ns = template_namespace(raw) if raw else None
    if ns:
        n = ns + '::' + n
    if '::' in n and not n.startswith(('std::', 'Concurrency::', 'Scaleform::', 'bnet')):
        outer = n.split('::')[0]
        a = area_of(outer)
        if a not in ('other', None):
            return a
    if n.startswith(('std::', 'Concurrency::', 'type_info')) or n in ('exception', 'bad_alloc', 'bad_cast',
                                                                        'bad_typeid', 'bad_array_new_length'):
        return 'std'
    if n.startswith(('Scaleform::', 'GFx', 'GAS', 'GRenderer')) or '::Scaleform::' in n:
        return 'scaleform'
    if n.startswith('bnet::') or n.startswith('bnet'):
        return 'bnet'
    if re.match(r'^hk[a-zA-Z]', n):
        return 'havok'
    anc = {leaf(a) for a in ancestors}
    base = leaf(n)
    if MAGIC.search(base) or anc & {'ActiveEffect', 'MagicItem', 'MagicCaster'}:
        return 'magic'
    if re.match(r'Ni[A-Z]', base):
        return 'netimmerse'
    if re.match(r'BS[A-Z]', base):
        return 'bsengine'
    if base in ep.ACTOR_CLASSES or base.endswith('Process') or 'Actor' in anc:
        return 'actors'
    a = ep.area_for(base) if base else None
    if a:
        return a
    if 'TESForm' in anc:
        return 'forms'
    return 'other'


# ---------------------------------------------------------------------------------------------
# meh321's name list (by Address Library id).

def read_meh321(path):
    out = {}
    if not path or not Path(path).is_file():
        return out
    for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        name = re.sub(r'_\*$', '', parts[1].strip())
        out[int(parts[0])] = name
    return out


def meh321_placeholder(name):
    """Names that only say which class a slot belongs to (`Class::Func12`, `Class::sub`)."""
    method = name.split('::')[-1]
    return bool(re.fullmatch(r'(?:Func|Unk_?|sub_?|unk_?)[0-9A-Fa-f]*', method)) or '::' not in name and \
        bool(re.fullmatch(r'(?:sub|Func|unk)_?[0-9A-Fa-f]*', name))


# ---------------------------------------------------------------------------------------------

def build(cfg, ghidra_dir, out_dir, rerun_ghidra=False, rerun_disasm=False):
    timing = {}
    t = time.monotonic()
    target, img, addrlib, comms = ep.setup(cfg)
    ng, po3 = comms[0], (comms[1] if len(comms) > 1 else None)
    timing['setup_s'] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    if rerun_ghidra or not (ghidra_dir / 'meta.tsv').is_file():
        ep.run_ghidra(cfg, '@all', ghidra_dir, 'refs', ghidra_dir.with_suffix('.log'))
        timing['ghidra_run_s'] = round(time.monotonic() - t, 1)
    meta = ep.load_meta(ghidra_dir)
    timing['ghidra_load_s'] = round(time.monotonic() - t, 1)
    funcs = {rva: m for rva, m in meta.items() if m['found']}
    base = ep.image_base(img)

    t = time.monotonic()
    cache = out_dir / 'cache' / f'disasm-{img.sha256[:12]}.pkl'
    if rerun_disasm and cache.is_file():
        cache.unlink()
    dis = run_disasm(cfg, {r: m['ranges'] for r, m in funcs.items()}, base, set(funcs), cache)
    timing['disasm_s'] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    groups = pogo_groups(img)
    gstarts = [g[0] for g in groups]

    def group_of(rva):
        i = bisect.bisect_right(gstarts, rva) - 1
        while i >= 0:
            r, s, n = groups[i]
            if r <= rva < r + s:
                return n
            if n.startswith('.text'):
                break
            i -= 1
        return None

    entries = set(funcs) | set(img.pdata_begins)
    rtti = Rtti(img, lambda r: r in entries)
    by_id = {}
    for rva, ids in addrlib['by_rva'].items():
        for i in ids:
            by_id[i] = rva
    timing['image_s'] = round(time.monotonic() - t, 1)

    # Classes with a primary vftable.
    t = time.monotonic()
    classes, by_raw = {}, {}
    for vt, (off, td, chd) in sorted(rtti.vftables.items()):
        raw = rtti.td_name(td)
        if off != 0:
            continue
        try:
            chain, allb = rtti.chain(chd)
        except Exception:
            chain, allb = [raw], [raw]
        if raw in by_raw:
            by_raw[raw]['other_primary_vftables'] += 1
            continue
        c = {'class': demangle_type(raw), 'rtti': raw, 'ng_key': ng_style(raw), 'vftable': vt,
             'slots': rtti.slots[vt], 'chain': chain, 'bases': allb[1:], 'other_primary_vftables': 0,
             'secondary_vftables': []}
        classes[c['class']] = c
        by_raw[raw] = c
    for vt, (off, td, chd) in sorted(rtti.vftables.items()):
        if off != 0 and rtti.td_name(td) in by_raw:
            by_raw[rtti.td_name(td)]['secondary_vftables'].append({'rva': vt, 'offset': off,
                                                                  'slots': len(rtti.slots[vt])})
    for c in classes.values():
        p = by_raw.get(c['chain'][1]) if len(c['chain']) > 1 else None
        c['parent'] = p['class'] if p else None
        c['ancestors'] = [demangle_type(x) for x in c['chain'][1:]]

    # Slot attribution: an implementation belongs to the most basic class whose vftable holds it
    # at that slot first, not to the derived class the walk happens to visit.
    slot_owner = {}
    for c in classes.values():
        for k, f in enumerate(c['slots']):
            owner = c
            while owner.get('parent'):
                p = classes[owner['parent']]
                if k < len(p['slots']) and p['slots'][k] == f:
                    owner = p
                else:
                    break
            prev = slot_owner.get(f)
            if prev is None or len(classes[owner['class']]['chain']) < len(classes[prev[0]]['chain']):
                slot_owner[f] = (owner['class'], k)
    secondary_owner = {}
    for c in classes.values():
        for sv in c['secondary_vftables']:
            for k, f in enumerate(rtti.slots[sv['rva']]):
                secondary_owner.setdefault(f, (c['class'], k))
    holders = defaultdict(set)
    for c in classes.values():
        for f in c['slots']:
            holders[f].add(c['class'])

    # Object size from the scalar deleting destructor: the size argument (EDX) of the sized
    # operator delete it calls. The delete is recognised as the callee most of slot 0's sites use.
    dcount = Counter()
    for c in classes.values():
        if c['slots']:
            for callee, imm, kind in dis['edx_calls'].get(c['slots'][0], []):
                dcount[callee] += 1
    total = sum(dcount.values()) or 1
    deletes = {f for f, n in dcount.items() if n >= 0.02 * total}
    timing['classes_s'] = round(time.monotonic() - t, 1)

    # Community declarations.
    t = time.monotonic()
    cache_dir = REPO / '.local/packs/_cache'
    decls = {'ng': scan_community(cfg['ng_root'], cache_dir / f'classes2-ng-{cfg["ng_revision"][:12]}.json')}
    if po3:
        decls['po3'] = scan_community(cfg['po3_root'], cache_dir / f'classes2-po3-{cfg["po3_revision"][:12]}.json')
    vt_ids = ep.vtable_index(comms)
    timing['community_s'] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    for c in sorted(classes.values(), key=lambda c: len(c['chain'])):
        size, how = None, None
        own_dtor = c['slots'][0] if c['slots'] else None
        parent = classes.get(c['parent']) if c['parent'] else None
        if own_dtor is not None and parent and parent['slots'] and parent['slots'][0] == own_dtor:
            how = 'inherits the parent\'s deleting destructor'
        elif own_dtor is not None:
            sizes = sorted({imm for callee, imm, kind in dis['edx_calls'].get(own_dtor, []) if callee in deletes})
            if len(sizes) == 1:
                size, how = sizes[0], 'operator delete size argument in slot 0'
            elif sizes:
                how = 'several delete sizes in slot 0'
            else:
                how = 'no sized delete in slot 0'
        c['size'], c['size_how'] = size, how
        chain_leaves = {leaf(demangle_type(x)) for x in c['chain']}
        c['community'] = {}
        key = c['ng_key']
        for src, (cdecl, sizes) in decls.items():
            entry = cdecl.get(key) if key else None
            if entry is None:
                continue
            # RTTI name check: the community VTABLE_ id must land on this class's own vftable.
            ae = vt_ids.get(key)
            vt_rva = by_id.get(ae) if ae is not None else None
            rtti_match = (vt_rva == c['vftable']) if vt_rva is not None else None
            inherited_destructors = set()
            ancestor = parent
            while ancestor:
                checked = ancestor.get('community', {}).get(src, {})
                if checked.get('passes'):
                    inherited_destructors.update(k for k, name in checked['names'].items()
                                                 if name.startswith('~'))
                ancestor = classes.get(ancestor.get('parent'))
            d = primary_slots(entry, chain_leaves, inherited_destructors)
            asserted = sizes.get(entry['name'], []) if entry['name'] == leaf(c['class']) else []
            chk = class_checks(d, c['slots'], parent['slots'] if parent else None, asserted, size, rtti_match,
                               entry['bases'][0] if entry['bases'] else None,
                               demangle_type(c['chain'][1]) if len(c['chain']) > 1 else None)
            chk['path'] = entry['path']
            chk['names'] = {k: d[k][0] for k in chk['usable_slots']}
            chk['declarations'] = {k: d[k][2] for k in chk['usable_slots'] if d[k][2]}
            c['community'][src] = chk
        c['passes'] = sorted(s for s, chk in c['community'].items() if chk['passes'])
        c['area'] = area_of(c['class'], c['ancestors'], c['rtti'])

    # Slot names per class: own declaration first, then the ancestors that introduced the slot,
    # NG before po3, each only from a class whose checks passed for that source.
    def slot_name(cname, k):
        cur = classes.get(cname)
        while cur:
            for src in ('ng', 'po3'):
                chk = cur['community'].get(src)
                if chk and chk['passes'] and k in chk['names']:
                    return chk['names'][k], src + '-slot', cur['class'], chk.get('declarations', {}).get(k)
            cur = classes.get(cur['parent']) if cur.get('parent') else None
        return None
    timing['checks_s'] = round(time.monotonic() - t, 1)

    # Names by Address Library id.
    t = time.monotonic()
    meh_path = cfg.get('meh321_names')
    meh = read_meh321(meh_path)
    if meh_path and Path(meh_path).is_file() and not cfg.get('meh321_revision'):
        cfg['meh321_revision'] = hashlib.sha256(Path(meh_path).read_bytes()).hexdigest()[:12]

    def id_names(rva):
        ids = addrlib['by_rva'].get(rva, [])
        out = []
        for src, comm in (('ng-id', ng), ('po3-id', po3)):
            if comm is None:
                continue
            for n in comm.names(ids):
                if n['kind'] in ('vtable', 'rtti', 'nirtti', 'data', 'offset') and n['how'] == 'table' and \
                        n['kind'] != 'offset':
                    continue
                out.append({'name': ep.short_name(n['name']), 'source': src, 'how': n['how'], 'ae_id': n['ae_id']})
        for i in ids:
            if i in meh:
                out.append({'name': meh[i], 'source': 'meh321', 'how': 'placeholder' if meh321_placeholder(meh[i])
                            else 'name', 'ae_id': i})
        return out

    # Callers.
    callers = defaultdict(set)
    for f, cs in dis['callees'].items():
        for c2 in cs:
            callers[c2].add(f)
    for f, cs in dis['tail_callees'].items():
        for c2 in cs:
            callers[c2].add(f)

    # Funclet parents, for EH outlines and for attributing funclets.
    timing['names_s'] = round(time.monotonic() - t, 1)
    t = time.monotonic()
    rows = []
    refs_iter = ep.iter_refs(ghidra_dir)
    pending = next(refs_iter, None)
    owned = defaultdict(list)
    for rva in sorted(meta):
        m = meta[rva]
        grefs = []
        while pending is not None and pending[0] < rva:
            pending = next(refs_iter, None)
        if pending is not None and pending[0] == rva:
            grefs = pending[1]
        if not m['found']:
            continue
        name = m['ghidra_name']
        group = group_of(rva)
        first = dis['first'].get(rva)
        kind = 'ordinary'
        if name.startswith(FUNCLET_PREFIXES) or (group or '').startswith('.text$x'):
            kind = 'eh-funclet'
        elif first and first[0] == 'jmp' and first[2] is not None and (first[2] - base) in img.imports:
            kind = 'import-thunk'
        elif m['thunk']:
            kind = 'thunk'
        elif group == '.text$di':
            kind = 'static-initializer'
        elif group == '.text$yd':
            kind = 'teardown'
        row = {'rva': rva, 'kind': kind, 'group': group, 'ghidra_size': sum(b - a for a, b in m['ranges']),
               'instructions': dis['n_instr'].get(rva, 0)}
        # Unwind and EH facts.
        entry = img.pdata_at.get(rva)
        eh = {'has_pdata': entry is not None, 'handler': None, 'handler_kind': None, 'states': None,
              'try_blocks': None, 'ip_map': None}
        if entry:
            try:
                u = img.unwind(entry[1])
                if u['flags'] & 3 and not u['flags'] & 4:
                    flags, length = ep.unwind_header(img.read(entry[1], 4), 'unwind info')
                    (h_rva,) = struct.unpack('<I', img.read(entry[1] + length, 4))
                    hname = ep.handler_name(img, h_rva, addrlib, comms)
                    eh['handler'] = hname or hex(h_rva)
                    eh['handler_kind'] = ('c++' if hname in CXX_HANDLERS else 'seh' if hname in (
                        '__C_specific_handler', '__GSHandlerCheck_SEH') else 'gs' if hname == '__GSHandlerCheck'
                        else 'other')
                    o = eh_outline(img, rva, entry[1], hname)
                    if o and o.get('states') is not None:
                        eh['states'] = len(o['states'])
                        eh['try_blocks'] = len(o['try_blocks'])
                        eh['ip_map'] = len(o['ip_to_state'])
                eh['chained'] = bool(u['flags'] & 4)
            except Exception as exc:  # unreadable unwind data is a fact about the function, not a crash
                eh['error'] = str(exc)[:80]
        row['eh'] = eh
        # Comparator v2 suitability, by the exporter's own rules.
        if kind in ('ordinary', 'static-initializer', 'teardown', 'thunk', 'import-thunk'):
            try:
                fact = ep.classify(img, addrlib, comms, rva, m, grefs)
                row['size'] = fact.get('size')
                if set(fact['reasons']) & {'split-body', 'pdata-not-at-entry', 'multiple-pdata', 'not-a-function'}:
                    # The v2 extent of a refused body can reach a distant chunk; count what the analysis holds.
                    row['size'] = row['ghidra_size']
                row['v2'] = {'verdict': fact['verdict'], 'reasons': fact['reasons'],
                             'cautions': sorted({c.split(':')[0].split(' 0x')[0] for c in fact['cautions']}),
                             'funclets': len(fact.get('eh', {}).get('funclets', []))}
            except Exception as exc:
                row['size'] = row['ghidra_size']
                row['v2'] = {'verdict': 'unsupported', 'reasons': ['exporter-error'], 'cautions': [str(exc)[:80]]}
        else:
            row['size'] = row['ghidra_size']
            row['v2'] = None
        # Names and owner.
        names = id_names(rva)
        so = slot_owner.get(rva)
        if so:
            sn = slot_name(so[0], so[1])
            if sn:
                method, src, introduced, _ = sn
                if method.startswith('~'):
                    method = '~' + leaf(so[0])
                names.append({'name': f'{so[0]}::{method}', 'source': src, 'how': f'slot {so[1]}',
                              'declared_in': introduced})
        owner = None
        if so:
            owner = {'class': so[0], 'how': 'vtable', 'slot': so[1], 'holders': len(holders[rva])}
        elif rva in secondary_owner:
            owner = {'class': secondary_owner[rva][0], 'how': 'vtable-secondary', 'slot': secondary_owner[rva][1]}
        else:
            for n in names:
                cls = ep.owning_class(n['name'])
                if cls and n['how'] != 'placeholder':
                    how = 'community-id' if n['source'] in ('ng-id', 'po3-id') else 'addrlib-name'
                    owner = {'class': cls, 'how': how, 'source': n['source']}
                    break
            if owner is None:
                for n in names:
                    cls = ep.owning_class(n['name'])
                    if cls:
                        owner = {'class': cls, 'how': 'addrlib-name', 'source': n['source']}
                        break
        row['owner'] = owner
        if owner and owner['how'].startswith('vtable'):
            # An id name whose class is not in the hierarchy holding the function contradicts the
            # image's own vftables; it stays listed but is not counted as a usable name.
            family = set()
            for h in set(holders.get(rva, ())) | {owner['class']}:
                family.add(leaf(h))
                family.update(leaf(a) for a in classes[h]['ancestors'] if h in classes)
            for n in names:
                if not n['source'].endswith('-slot'):
                    cls = ep.owning_class(n['name'])
                    # meh321 spells template classes Family_Arg_; compare those by family name.
                    n['agrees_with_vtable'] = bool(cls) and (leaf(cls) in family or any(
                        leaf(cls).startswith(f + '_') for f in family))
        row['names'] = names
        row['ae_ids'] = addrlib['by_rva'].get(rva, [])
        row['callers'] = len(callers.get(rva, ()))
        row['callees'] = dis['callees'].get(rva, [])
        row['tail_callees'] = dis['tail_callees'].get(rva, [])
        row['imports'] = len(dis['import_calls'].get(rva, []))
        keys = dis['keys'].get(rva)
        row['l1'], row['l2'] = keys if keys else (None, None)
        if owner and owner['how'] in ('vtable', 'vtable-secondary', 'community-id', 'addrlib-name') \
                and kind == 'ordinary':
            owned[owner['class']].append(rva)
        rows.append(row)
    timing['rows_s'] = round(time.monotonic() - t, 1)

    # Funclets: parent and what each one calls (the destructor that names the type it destroys).
    t = time.monotonic()
    by_rva = {r['rva']: r for r in rows}
    for r in rows:
        if r['kind'] == 'eh-funclet':
            pass
    # Address neighbourhood: an unattributed ordinary function between two functions of one class
    # within 4 KiB is a class guess only (guidelines: 25 of 43 checked cases).
    attributed = sorted((r['rva'], r['owner']['class']) for r in rows if r['owner'] and r['kind'] == 'ordinary')
    arvas = [a for a, _ in attributed]
    for r in rows:
        if r['owner'] or r['kind'] != 'ordinary':
            continue
        i = bisect.bisect_left(arvas, r['rva'])
        if 0 < i < len(arvas):
            (lo, lc), (hi, hc) = attributed[i - 1], attributed[i]
            if lc == hc and r['rva'] - lo <= 4096 and hi - r['rva'] <= 4096:
                r['owner'] = {'class': lc, 'how': 'rtti-adjacent', 'label': 'GUESS(low)'}
    # L1 cluster sizes.
    l1n = Counter(r['l1'] for r in rows if r['l1'] and r['kind'] == 'ordinary')
    for r in rows:
        r['cluster_size'] = l1n.get(r['l1'], 0) if r['l1'] else 0
    timing['post_s'] = round(time.monotonic() - t, 1)

    # Class rows: owned functions and bytes.
    for c in classes.values():
        fs = [by_rva[f] for f in owned.get(c['class'], []) if f in by_rva]
        c['functions'] = len(fs)
        c['bytes'] = sum(f['size'] or 0 for f in fs)
        c['own_slot_functions'] = sum(1 for k, f in enumerate(c['slots']) if slot_owner.get(f, (None,))[0] == c['class'])
        c['slot_names'] = {}
        for k in range(len(c['slots'])):
            sn = slot_name(c['class'], k)
            if sn:
                c['slot_names'][k] = {'name': sn[0], 'source': sn[1], 'declared_in': sn[2], 'declaration': sn[3]}
                continue
            # meh321's method name for the implementation in this slot, when its class agrees with
            # the hierarchy; the slot keeps the name wherever the implementation is inherited.
            f = by_rva.get(c['slots'][k])
            for n in (f or {}).get('names', []):
                if n['source'] == 'meh321' and n['how'] == 'name' and n.get('agrees_with_vtable'):
                    method = n['name'].split('::')[-1]
                    owner_cls = slot_owner.get(c['slots'][k], (c['class'],))[0]
                    if method == 'dtor':
                        method = '~' + leaf(owner_cls)
                    if re.fullmatch(r'~?[A-Za-z_]\w*', method):
                        c['slot_names'][k] = {'name': method, 'source': 'meh321', 'declared_in': owner_cls,
                                              'declaration': None}
                    break

    t = time.monotonic()
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / 'functions.jsonl', 'w') as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + '\n')
    with open(out_dir / 'classes.jsonl', 'w') as fh:
        for c in sorted(classes.values(), key=lambda c: c['class']):
            fh.write(json.dumps(c, sort_keys=True) + '\n')
    (out_dir / 'callsites.json').write_text(json.dumps({str(k): v for k, v in dis['census'].items()}))
    timing['write_s'] = round(time.monotonic() - t, 1)
    inputs = {'image_sha256': img.sha256, 'address_library': f'{addrlib["version"]} {addrlib["sha256"][:16]}',
              'ng_revision': cfg['ng_revision'], 'po3_revision': cfg.get('po3_revision'),
              'meh321_names': cfg.get('meh321_revision'), 'ghidra_dir': str(ghidra_dir),
              'delete_callees': len(deletes)}
    meta_out = {'schema': TABLE_SCHEMA, 'build_id': target['build_id'], 'inputs': inputs, 'timing': timing,
                'functions': len(rows), 'classes': len(classes)}
    (out_dir / 'table-meta.json').write_text(json.dumps(meta_out, indent=2) + '\n')
    return rows, classes, meta_out


AREA_ORDER = ('netimmerse', 'bsengine', 'forms', 'actors', 'magic', 'other', 'havok', 'scaleform', 'bnet', 'std',
              'unattributed')
MEASURED_OWNER = ('vtable', 'vtable-secondary', 'community-id', 'addrlib-name')


def display_class(name):
    """Class label for public aggregates: template instantiations folded into their family."""
    name = re.sub(r'<.*', '<>', name)
    if '$' in name or len(name) > 48:
        name = name.split('::')[0] + '::...'
    return name


def scope_areas(rows, classes, top=30):
    """Sanitized per-area and per-class breakdown of ordinary functions (no addresses).

    Every ordinary function lands in exactly one area: by the class its vftable or an approved id
    name gives (measured attribution), area by reconstruction/README.md (owning system, then
    prefix); the rest is `unattributed`, with the share that sits between two functions of one
    class reported as an estimate inside it."""
    per = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    adjacent = [0, 0]
    for r in rows:
        if r['kind'] != 'ordinary':
            continue
        size = r['size'] or 0
        owner = r.get('owner') or {}
        if owner.get('how') in MEASURED_OWNER:
            cname = owner['class']
            c = classes.get(cname)
            area = c['area'] if c else area_of(cname)
            key = display_class(cname)
        else:
            area, key = 'unattributed', None
            if owner.get('how') == 'rtti-adjacent':
                adjacent[0] += 1
                adjacent[1] += size
        cell = per[area][key]
        cell[0] += 1
        cell[1] += size
    blocks = []
    for area in AREA_ORDER:
        if area not in per:
            continue
        cl = per[area]
        fns, byt = sum(v[0] for v in cl.values()), sum(v[1] for v in cl.values())
        named = sorted(((k, v) for k, v in cl.items() if k), key=lambda kv: (-kv[1][1], kv[0]))
        b = {'id': area, 'label': AREA_LABELS[area], 'functions': fns, 'bytes': byt, 'basis': 'measured',
             'treatment': 'out_of_scope' if area in ('havok', 'scaleform', 'bnet', 'std') else 'in_scope',
             'classes': [{'name': k, 'functions': v[0], 'bytes': v[1], 'basis': 'measured'} for k, v in named[:top]]}
        rest = named[top:]
        if rest:
            b['other_classes'] = {'classes': len(rest), 'functions': sum(v[0] for _, v in rest),
                                  'bytes': sum(v[1] for _, v in rest), 'basis': 'measured'}
        if area == 'unattributed':
            b['method'] = ('Ordinary functions no vftable slot or approved id name ties to a class. Of them, '
                           f'{adjacent[0]:,} ({adjacent[1]:,} bytes) lie within 4 KiB between two functions of one '
                           'class: an address-neighbourhood estimate, not an attribution.')
            b['adjacent_estimate'] = {'functions': adjacent[0], 'bytes': adjacent[1], 'basis': 'estimated'}
        else:
            b['method'] = ('Ordinary functions whose class is known from the image RTTI vftables (the most basic '
                           'class holding the implementation) or an approved Address Library id name; area by '
                           'reconstruction/README.md, owning system then prefix.')
        blocks.append(b)
    return blocks


def write_scope(path, rows, classes, meta):
    scope = json.loads(Path(path).read_text())
    blocks = scope_areas(rows, classes)
    ordinary = [r for r in rows if r['kind'] == 'ordinary']
    scope['areas'] = {
        'note': ('Sanitized aggregates of the private function table (tools/ghidra/build_function_table.py): area '
                 'and class names with function counts and byte totals; no addresses, bytes or disassembly. '
                 'Class names come from the image RTTI or an approved naming source; template instantiations are '
                 'folded into their family.'),
        'population': {'functions': len(ordinary), 'bytes': sum(r['size'] or 0 for r in ordinary), 'basis': 'measured',
                       'method': ('Ghidra function entries that are not EH funclets, thunks, import thunks, static '
                                  'initializers or teardown functions (POGO .text$di, .text$yd). Size is the '
                                  'comparator v2 extent (.pdata with chained entries and switch tables), or the '
                                  'analysis body where v2 refuses the range.')},
        'classes_with_primary_vftable': {'value': len(classes), 'basis': 'measured',
                                         'method': 'CompleteObjectLocators reached through relocated pointers.'},
        'classes_passing_checks': {'value': sum(1 for c in classes.values() if c['passes']), 'basis': 'measured',
                                   'method': 'Checks C1 to C4, RTTI name and base chain of docs/resource-guidelines.md '
                                             'for at least one community header (CommonLibSSE-NG or the powerof3 fork).'},
        'blocks': blocks}
    if 'findings/fourth-batch-selection.md' not in scope.get('sources', []):
        scope.setdefault('sources', []).append('findings/fourth-batch-selection.md')
    Path(path).write_text(json.dumps(scope, indent=2) + '\n')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--config', default=str(ep.DEFAULT_CONFIG))
    p.add_argument('--ghidra-dir', default=None, help='Default: <out>/cache/ghidra-all')
    p.add_argument('--out', default=str(REPO / '.local/analysis'))
    p.add_argument('--rerun-ghidra', action='store_true')
    p.add_argument('--rerun-disasm', action='store_true')
    p.add_argument('--write-scope', default=None, metavar='data/scope.json',
                   help='Also write the sanitized area and class breakdown into this scope file')
    a = p.parse_args(argv)
    cfg = ep.load_config(a.config)
    out = Path(a.out)
    gdir = Path(a.ghidra_dir) if a.ghidra_dir else out / 'cache' / 'ghidra-all'
    t0 = time.monotonic()
    rows, classes, m = build(cfg, gdir, out, a.rerun_ghidra, a.rerun_disasm)
    m['timing']['total_s'] = round(time.monotonic() - t0, 1)
    (out / 'table-meta.json').write_text(json.dumps(m, indent=2) + '\n')
    if a.write_scope:
        write_scope(a.write_scope, rows, classes, m)
    kinds = Counter(r['kind'] for r in rows)
    print(json.dumps({'functions': len(rows), 'classes': len(classes), 'kinds': kinds, 'timing': m['timing']}))


if __name__ == '__main__':
    main()
