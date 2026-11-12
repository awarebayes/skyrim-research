"""Per-function facts of the pinned image for clustering and the inlined-body census.

For every function entry of a Ghidra export this computes, with the comparator's definitions:

- the compared range: the export's size, corrected to the end of the last instruction when the
  analysis stopped inside one, grown over chained `.pdata` entries and over switch tables after
  the code (the exporter's own `function_extent` and `switch_tables`, `tools/ghidra/export_pack.py`);
- the reference fields: every field a linker patches when the code comes from an MSVC `/Gy`
  object, i.e. what `tools/compare.py` compares as a relocation (`REL32`, `REL32_k`, `ADDR32NB`,
  and the `DIR64` fields contract v2 refuses), each with its target RVA, or `self+N` when the
  target lies in the function's own section (own labels, switch tables, recursion);
- a masked digest (bytes outside reference fields, field layout and kinds, self-relative targets,
  unwind codes) and an exact digest (raw bytes);
- owning classes from the image's RTTI vftables and names from the approved community sources
  joined through the Address Library.

Everything computed is game-derived; callers write it under `.local/` only. The module itself
holds no game data.
"""
import bisect
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'tools' / 'ghidra'))
sys.path.insert(0, str(HERE))
import x64  # noqa: E402

SCHEMA = 1


def pogo_groups(img):
    """[(rva, size, name)] from the image's POGO debug record (type 13), or []."""
    rva, size = img.dirs[6]
    out = []
    if not size:
        return out
    blob = img.blob
    for i in range(size // 28):
        typ, dsz, drva, draw = struct.unpack_from('<IIII', img.read(rva + 28 * i + 12, 16))
        if typ != 13:
            continue
        p = draw + 4
        while p < draw + dsz:
            r, s = struct.unpack_from('<II', blob, p)
            e = blob.index(b'\0', p + 8)
            out.append((r, s, blob[p + 8:e].decode('latin-1')))
            p = (e + 4) & ~3
        break
    return out


def group_of(groups_sorted, starts, rva):
    i = bisect.bisect_right(starts, rva) - 1
    if i >= 0:
        r, s, n = groups_sorted[i]
        if r <= rva < r + s:
            return n
    return None


def read_export(path):
    """(functions [(rva, size, name)], vftables {rva: (col offset, display name)}) of a Ghidra export."""
    funcs, vtables = [], {}
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for line in lines:
        p = line.split(None, 4)
        if not p:
            continue
        if p[0] == 'F' and len(p) >= 5:
            funcs.append((int(p[1], 16), int(p[2]), p[4].strip()))
        elif p[0] == 'V' and len(p) >= 4:
            q = line.split(None, 3)
            vtables[int(q[1], 16)] = (int(q[2]), q[3].strip())
    funcs.sort()
    return funcs, vtables


def is_funclet_name(name):
    return name.startswith(('Unwind@', 'Catch@', 'Catch_', 'Catch_All@', 'Filter@', 'Finally@'))


def field_records(code, rva, size, image_base, fn_end, table_start=None):
    """Decode [rva, rva+size) and list the reference fields.

    Returns (fields, insn list, flags). A field is (offset, width, kind, k, target) with kind
    'REL32' (k = bytes after the field), 'ADDR32NB', 'SHORT_EXTERNAL' (an 8-bit branch that leaves
    the function: no object can encode it, so the comparator would fail it) and target an RVA.
    `table_start`, when given, stops decoding there (switch tables follow the code).
    """
    stop = table_start if table_start is not None else size
    insns = []
    p = 0
    base_regs = set()
    fields = []
    flags = set()
    va = image_base + rva
    while p < stop:
        ins = x64.decode(code, p, va + p, len(code))
        insns.append((p, ins))
        if ins.rel is not None:
            t = ins.target - image_base
            if not (rva <= t < fn_end):
                if ins.rel[1] == 4:
                    fields.append((p + ins.rel[0], 4, 'REL32', 0, t))
                else:
                    flags.add('short-external-branch')
                    fields.append((p + ins.rel[0], 1, 'SHORT_EXTERNAL', 0, t))
        if ins.rip is not None:
            t = ins.rip_target - image_base
            k = ins.length - ins.rip - 4
            fields.append((p + ins.rip, 4, 'REL32', k, t))
            if ins.lea and t == 0:
                base_regs.add(ins.reg)
        elif ins.disp is not None and ins.disp[1] == 4 and base_regs and (ins.base in base_regs or ins.index in base_regs):
            fields.append((p + ins.disp[0], 4, 'ADDR32NB', 0, ins.disp[2] & 0xFFFFFFFF))
        if ins.flow in (x64.IJMP,):
            flags.add('indirect-jump')
        p += ins.length
    return fields, insns, flags, p


class Image:
    """The pinned image plus its export, RTTI and community names, analysed per function."""

    def __init__(self, image_path, export_path, addrlib_path=None, communities=()):
        import export_pack
        self.ep = export_pack
        self.img = export_pack.ImageFacts(image_path)
        self.image_base = self.img.pe.image_base
        self.funcs, self.vtables_raw = read_export(export_path)
        self.starts = [f[0] for f in self.funcs]
        self.index = {f[0]: i for i, f in enumerate(self.funcs)}
        groups = sorted(pogo_groups(self.img))
        self.groups = groups
        gstarts = [g[0] for g in groups]
        self.group = [group_of(groups, gstarts, f[0]) for f in self.funcs]
        self.addrlib = export_pack.read_addrlib_v5(addrlib_path) if addrlib_path else None
        self.communities = list(communities)
        self._rtti()

    # -- RTTI ---------------------------------------------------------------------------------
    def _u32(self, rva):
        try:
            return struct.unpack('<I', self.img.read(rva, 4))[0]
        except Exception:
            return None

    def _u64(self, rva):
        try:
            return struct.unpack('<Q', self.img.read(rva, 8))[0]
        except Exception:
            return None

    def _td_name(self, td):
        try:
            return self.img._cstr(td + 16)
        except Exception:
            return None

    def _rtti(self):
        """vftable slots, class of each vftable, and RTTI ancestors of each class."""
        base = self.image_base
        fset = self.index
        vstarts = set(self.vtables_raw)
        self.vtables = {}
        self.class_of_vtable = {}
        self.ancestors = {}
        self.display = {}
        for v, (coloff, display) in self.vtables_raw.items():
            slots = []
            k = 0
            while True:
                if k and v + 8 * k in vstarts:
                    break
                q = self._u64(v + 8 * k)
                if q is None or not (base < q < base + 0x10000000) or (q - base) not in fset:
                    break
                slots.append(q - base)
                k += 1
            self.vtables[v] = slots
            col = self._u64(v - 8)
            if col is None:
                continue
            col -= base
            td, chd = self._u32(col + 12), self._u32(col + 16)
            raw = self._td_name(td) if td else None
            if not raw:
                continue
            self.class_of_vtable[v] = (raw, coloff)
            self.display.setdefault(raw, display)
            if raw not in self.ancestors and chd:
                nb, bca = self._u32(chd + 8), self._u32(chd + 12)
                names = []
                for i in range(min(nb or 0, 64)):
                    bcd = self._u32(bca + 4 * i)
                    tdn = self._td_name(self._u32(bcd)) if bcd else None
                    if tdn:
                        names.append(tdn)
                self.ancestors[raw] = names
        self.slot_refs = {}
        for v, slots in self.vtables.items():
            for k, f in enumerate(slots):
                self.slot_refs.setdefault(f, []).append((v, k))

    def owner(self, rva):
        """(class display name or None, template?, slot list) for a function held in vftables.

        An implementation seen through several classes belongs to the most-base class whose
        vftable holds it (docs/resource-guidelines.md, po3 rules); several unrelated classes give
        no owner.
        """
        refs = self.slot_refs.get(rva)
        if not refs:
            return None, False, []
        classes = []
        for v, k in refs:
            c = self.class_of_vtable.get(v)
            if c and c[0] not in classes:
                classes.append(c[0])
        if not classes:
            return None, False, refs
        best = None
        for c in classes:
            if all(c == o or c in self.ancestors.get(o, []) for o in classes):
                best = c
                break
        if best is None:
            return None, False, refs
        disp = self.display.get(best, best)
        return disp, best.startswith(('.?AV?$', '.?AU?$')), refs

    # -- names --------------------------------------------------------------------------------
    def community_names(self, rva):
        """[(name, source label, licence, how)] for the Address Library ids at `rva`."""
        if not self.addrlib:
            return []
        out = []
        ids = self.addrlib['by_rva'].get(rva, [])
        for c in self.communities:
            for n in c.names(ids):
                if n['kind'] in ('vtable', 'rtti', 'nirtti'):
                    continue
                out.append((n['name'].replace('RE::Offset::', '').replace('RE::', ''), c.label, c.licence, n['how']))
        return out

    def best_name(self, rva):
        names = self.community_names(rva)
        for n in names:
            if n[3] == 'table':
                return n
        return names[0] if names else None

    # -- per function -------------------------------------------------------------------------
    def analyse(self, i):
        """Facts of function i, or a dict with 'error' when the bytes do not decode."""
        rva, export_size, name = self.funcs[i]
        img = self.img
        try:
            sec = img.section(rva)
            avail = sec.vaddr + min(sec.vsize or sec.raw_size, sec.raw_size) - rva
            code = img.read(rva, min(avail, export_size + 64 * 1024))
        except Exception as exc:
            return {'rva': rva, 'error': 'unreadable: %s' % exc}
        nxt = self.starts[i + 1] if i + 1 < len(self.starts) else rva + len(code)
        try:
            fields, insns, flags, code_end_off = field_records(code, rva, export_size, self.image_base,
                                                               rva + max(export_size, 1))
        except x64.DecodeError as exc:
            return {'rva': rva, 'error': 'decode: %s' % exc}
        code_end = rva + max(code_end_off, export_size)
        end, chained, split = self.ep.function_extent(img, rva, code_end)
        if end != rva + export_size:
            try:
                fields, insns, mflags, moff = field_records(code, rva, end - rva, self.image_base, end)
            except x64.DecodeError as exc:
                return {'rva': rva, 'error': 'decode: %s' % exc}
            flags |= mflags
            end = max(end, rva + moff)
        data_targets = {f[4] for f in fields if f[2] in ('REL32', 'ADDR32NB')}
        try:
            table_end, entries = self.ep.switch_tables(img, rva, end, data_targets)
        except Exception:
            # A function at the very end of its section has no room for a table after it.
            table_end, entries = end, 0
        size = table_end - rva
        if size > len(code):
            return {'rva': rva, 'error': 'range past readable code'}
        if entries:
            tstart = ((end + 3) & ~3) - rva
            for j in range(entries):
                t = struct.unpack_from('<I', code, tstart + 4 * j)[0]
                fields.append((tstart + 4 * j, 4, 'ADDR32NB', 0, t))
        dir64 = img.dir64_in(rva, rva + size)
        for d in dir64:
            q = struct.unpack('<Q', img.read(d, 8))[0]
            fields.append((d - rva, 8, 'DIR64', 0, q - self.image_base))
            flags.add('addr64')
        fields.sort()
        if split:
            flags.add('split-body')
        if size != export_size:
            flags.add('size-corrected')
        body = code[:size]
        masked = bytearray(body)
        layout = []
        targets = []
        for off, width, kind, k, target in fields:
            for j in range(off, min(off + width, size)):
                if 0 <= j:
                    masked[j] = 0
            if rva <= target < rva + size:
                layout.append((off, width, kind, k, 'self+%d' % (target - rva)))
            else:
                layout.append((off, width, kind, k, None))
                targets.append((off, kind, target))
        unwind = b''
        handler = None
        pd = img.pdata_at.get(rva)
        if pd:
            try:
                head = img.read(pd[1], 4)
                cnt = head[2]
                unwind = img.read(pd[1], 4 + 2 * cnt)
                if (head[0] >> 3) & 3:
                    length = 4 + 2 * ((cnt + 1) & ~1)
                    handler = struct.unpack('<I', img.read(pd[1] + length, 4))[0]
            except Exception:
                unwind = b'?'
        parts = [(b - rva, e - rva) for b, e, _ in chained]
        h = hashlib.blake2b(digest_size=12)
        h.update(bytes(masked))
        h.update(repr(layout).encode())
        h.update(unwind)
        h.update(repr(parts).encode())
        h.update(b'eh' if handler is not None else b'-')
        exact = hashlib.blake2b(body, digest_size=12).hexdigest()
        # L2: displacements and immediates also blanked, so accessors of other offsets and
        # constant returns of other values share a shape.
        shape = bytearray(masked)
        operands = []
        for off, ins in insns:
            for part in (ins.disp, ins.imm):
                if part is not None:
                    a, n = off + part[0], part[1]
                    operands.append((a, n, int.from_bytes(body[a:a + n], 'little', signed=True)))
                    shape[a:a + n] = bytes(n)
        h2 = hashlib.blake2b(digest_size=12)
        h2.update(bytes(shape))
        h2.update(repr(layout).encode())
        h2.update(unwind)
        h2.update(repr(parts).encode())
        h2.update(b'eh' if handler is not None else b'-')
        return {'rva': rva, 'size': size, 'export_size': export_size, 'name': name,
                'masked': h.hexdigest(), 'exact': exact, 'shape': h2.hexdigest(), 'operands': operands,
                'targets': targets,
                'nfields': len(fields), 'flags': sorted(flags), 'eh': handler is not None,
                'handler': handler, 'pdata': pd is not None, 'chained': len(chained),
                'table_entries': entries, 'ninsns': len(insns), 'next': nxt,
                '_insns': insns, '_code': body}


def load_config(path):
    cfg = json.loads(Path(path).read_text())
    return cfg


def open_image(cfg, export_path, with_names=True):
    """An Image from an exporter-style config; community names only when the checkouts exist."""
    comms = []
    if with_names:
        import export_pack
        cache = Path(cfg.get('cache_dir') or (REPO / '.local/packs/_cache'))
        for label, root_key, rev_key, licence in (('CommonLibSSE-NG', 'ng_root', 'ng_revision', 'MIT'),
                                                  ('powerof3/CommonLibSSE', 'po3_root', 'po3_revision',
                                                   'GPL-3.0, local use only')):
            root = cfg.get(root_key)
            if root and Path(root).is_dir():
                comms.append(export_pack.Community(label, root, cfg[rev_key], licence, cache))
    return Image(cfg['image'], export_path, cfg.get('addrlib') if with_names else None, comms)


NAME_CLASS = re.compile(r'^(?:[\w<>,]+::)*([\w<>,]+)::[~\w]+$')


def class_of_name(name):
    """`A::B::Method` -> `A::B`, or None for a free name."""
    if not name or '::' not in name:
        return None
    return name.rsplit('::', 1)[0]
