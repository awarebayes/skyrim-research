#!/usr/bin/env python3
"""Aligned diagnostics for one function: how far a candidate is from the target, and why.

    tools/verifier/align.py --attempt <task-dir>/attempts/<NNN> [--task-dir <task-dir>] [--all]
    tools/verifier/align.py --target T.txt --candidate C.txt [--symbols symbols.json] [--rva 0x...] [--out DIR]
    tools/verifier/align.py --object candidate.obj --symbol SYM --rva 0x... --size N [--symbols ...] [--out DIR]

Inputs are `llvm-objdump -d [-r] --x86-asm-syntax=intel` listings, produced the same way as
`disasm.py` does (same objdump lookup, same local image from .local/verifier/config.json). The
listings are game-derived (G2): the aligned listing goes only to the private attempt directory.
The printed summary and the JSON carry no instruction bytes and no instruction text: offsets,
class names, register names and counts only. A reading aid and a search score, never evidence;
the comparator alone decides a match.

Normalisation. Each instruction becomes mnemonic (with its lock/rep prefix) plus operand shapes:
registers abstracted to their width (rsp and rip kept), memory operands as size, base/index shape,
scale and displacement, immediates kept, rip-relative operands and direct call/jump targets
replaced by the referenced RVA (target: decoded address minus image base; candidate: relocation
symbol looked up in the task's symbol map, plus the addend), and branches inside the function
replaced by a label whose correspondence is checked through the alignment. Relocated fields hold
placeholders in the candidate and are masked before bytes are compared.

Alignment. Global weighted edit alignment over normalised instructions (gap 1; substitution of
a related instruction 1.2, so that two swapped rows become two gaps rather than two
substitutions; unrelated 2). Unpaired instructions are then re-paired: an identical instruction
within a few rows is a reorder; runs of unpaired instructions that align with each other across
blocks are a moved block. Register renaming is discovered from the paired
instructions as the most frequent target-to-candidate correspondence, made a bijection greedily.

Distance. d = prologue + body + refs, each the sum of the weights below over the differences
assigned to it (frame instructions and unwind fields -> prologue; callee and data-reference
differences -> refs; everything else -> body):

    1.0   missing, extra or different instruction (an extra or missing call included)
    1.0   reference to a different symbol or address
    0.5   operand width or signedness; constant or displacement; branch polarity or a branch
          into a non-corresponding block; one reordered or moved instruction; one instruction
          whose registers break the renaming map; one unwind field not explained by the map
    0.5   one renamed register pair that involves a caller-saved register
    0.25  one renamed callee-saved register pair (pure allocation choice); one unresolved reference
    0.1   one instruction whose bytes differ although its normalised form is equal (encoding)

d is 0 exactly when every instruction's bytes are equal outside relocated fields, every reference
resolves to the target's, and the unwind codes (when given) are equal. It is additive over
non-negative terms, so a source change that removes differences without adding others lowers
it; every cookbook fix is of that kind. A pure two-register callee-saved swap scores 0.5.
"""
import argparse
import bisect
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disasm  # noqa: E402

SCHEMA = 1
# The byte column ends at a tab (or a run of spaces); a long instruction's last byte is followed
# by the tab directly, so "bytes followed by a space" would swallow it into the text.
INSN = re.compile(r'^\s*([0-9a-f]+):\s+([0-9a-f]{2}(?: [0-9a-f]{2})*)(?:\s*\t|\s{2,})\s*(\S.*)$')
RELOC = re.compile(r'^\s*([0-9a-f]+):\s+(IMAGE_REL_\S+)\s+(\S+)')
PREFIXES = {'lock', 'rep', 'repe', 'repne', 'repz', 'repnz', 'notrack', 'data16', 'rex64'}

WEIGHT = {
    'missing': 1.0, 'extra': 1.0, 'different': 1.0, 'wrong-ref': 1.0,
    'width': 0.5, 'constant': 0.5, 'branch': 0.5, 'moved': 0.5, 'inconsistent-reg': 0.5,
    'unwind-field': 0.5, 'rename-volatile': 0.5,
    'rename-callee-saved': 0.25, 'unresolved-ref': 0.25,
    'encoding': 0.1,
}

# The fixed vocabulary; the cookbook rules below are keyed by these names.
CLASSES = ('register-renaming', 'extra-instruction', 'missing-instruction', 'operand-width-or-signedness',
           'reordered-instructions', 'block-order-or-branch-polarity', 'prologue-or-unwind',
           'callee-or-argument-setup', 'constant-or-displacement', 'reference-target',
           'different-instruction', 'encoding')

# docs/matching-cookbook.md rule numbers; one place to update if the cookbook is renumbered.
COOKBOOK = {
    1: 're-read a pointer the target re-tests for null',
    2: 'reorder a two-way check (early returns, one call site)',
    3: 'an inlined helper called twice (loop condition and body)',
    4: 'compute in source order, or a predicate helper called twice',
    5: 'a live argument register: the callee takes that argument',
    6: 'change the width or signedness of the switch operand or temporary',
    7: 'a shared constant: put the value-producing branch in a helper',
    8: 'an early return false inside a bool helper',
    9: 'drop the initialiser of a local a callee fills',
    10: 'class operator new/delete: one deleting-destructor call',
    11: 'missing virtual slots shift the vtable displacement',
    12: 'pure callee-saved register swap: stop the source search, send to triage',
    13: 'EH state slot (-2 store) without a handler: send to triage',
}

# Most specific symptom first: the first recognised rule becomes the suggestion.
RULE_PRIORITY = (12, 13, 5, 10, 11, 1, 9, 7, 6, 3, 8, 2, 4)

_GPR = {}
for _c, _names in {
        'rax': ('rax', 'eax', 'ax', 'al'), 'rbx': ('rbx', 'ebx', 'bx', 'bl'),
        'rcx': ('rcx', 'ecx', 'cx', 'cl'), 'rdx': ('rdx', 'edx', 'dx', 'dl'),
        'rsi': ('rsi', 'esi', 'si', 'sil'), 'rdi': ('rdi', 'edi', 'di', 'dil'),
        'rbp': ('rbp', 'ebp', 'bp', 'bpl'), 'rsp': ('rsp', 'esp', 'sp', 'spl')}.items():
    for _w, _n in zip((64, 32, 16, 8), _names):
        _GPR[_n] = (_c, _w)
for _c, _h in (('rax', 'ah'), ('rbx', 'bh'), ('rcx', 'ch'), ('rdx', 'dh')):
    _GPR[_h] = (_c, 'h8')
for _i in range(8, 16):
    for _w, _s in zip((64, 32, 16, 8), ('', 'd', 'w', 'b')):
        _GPR[f'r{_i}{_s}'] = (f'r{_i}', _w)
for _i in range(16):
    _GPR[f'xmm{_i}'] = (f'xmm{_i}', 128)
    _GPR[f'ymm{_i}'] = (f'xmm{_i}', 256)
_GPR['rip'] = ('rip', 64)

CALLEE_SAVED = {'rbx', 'rbp', 'rsi', 'rdi', 'r12', 'r13', 'r14', 'r15'} | {f'xmm{i}' for i in range(6, 16)}
ARG_REGS = {'rcx', 'rdx', 'r8', 'r9', 'xmm0', 'xmm1', 'xmm2', 'xmm3'}
FIXED = {'rsp', 'rip'}
UNWIND_REGS = ('rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi',
               'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15')

_INVERSE = {}
for _a, _b in (('je', 'jne'), ('jb', 'jae'), ('ja', 'jbe'), ('jl', 'jge'), ('jg', 'jle'),
               ('js', 'jns'), ('jo', 'jno'), ('jp', 'jnp')):
    _INVERSE[_a], _INVERSE[_b] = _b, _a
_SIGN_PAIRS = {frozenset(p) for p in (('l', 'b'), ('ge', 'ae'), ('g', 'a'), ('le', 'be'))}
_MOVES = {'mov', 'movzx', 'movsx', 'movsxd'}
_COMPARES = {'cmp', 'test', 'and'}
_SHIFTS = {'shl', 'shr', 'sar', 'sal'}
_WRITES_FIRST = {'mov', 'lea', 'xor', 'movzx', 'movsx', 'movsxd', 'movss', 'movsd', 'movaps', 'movups',
                 'movq', 'movd', 'or', 'and', 'add', 'sub', 'inc', 'dec', 'shl', 'shr', 'sar', 'imul',
                 'cvtsi2ss', 'cvtsi2sd', 'xorps', 'pxor'}


def _num(text):
    text = text.strip()
    neg = text.startswith('-')
    if neg:
        text = text[1:]
    value = int(text, 16) if text.lower().startswith('0x') else int(text)
    return -value if neg else value


def _is_num(text):
    return bool(re.fullmatch(r'-?(0x[0-9a-fA-F]+|\d+)', text.strip()))


def _cond(mnem):
    for head in ('cmov', 'set', 'j'):
        if mnem.startswith(head) and mnem != 'jmp':
            return head, mnem[len(head):]
    return None, None


class Insn:
    __slots__ = ('idx', 'addr', 'off', 'data', 'text', 'mnem', 'shape', 'regs', 'ref', 'dest', 'relocs',
                 'internal', 'label', 'block', 'mask', 'frame')

    def __repr__(self):
        return f'Insn({self.off:#x} {self.text!r})'

    @property
    def is_jcc(self):
        return self.mnem.startswith('j') and self.mnem != 'jmp'

    @property
    def is_branch(self):
        return self.mnem.startswith('j')

    @property
    def is_call(self):
        return self.mnem == 'call'

    @property
    def ends_block(self):
        return self.is_branch or self.mnem in ('ret', 'int3', 'ud2')


def parse_listing(text):
    """[(address, [byte hex], text, [(field address, reloc type, symbol)])], prefix rows merged into the next."""
    rows, pending = [], None
    for line in text.splitlines():
        r = RELOC.match(line)
        if r and rows:
            rows[-1][3].append((int(r.group(1), 16), r.group(2).replace('IMAGE_REL_AMD64_', ''), r.group(3)))
            continue
        m = INSN.match(line)
        if not m:
            continue
        addr, data, body = int(m.group(1), 16), m.group(2).split(), ' '.join(m.group(3).split())
        if body in PREFIXES:
            # llvm-objdump prints a lone `lock` row; the prefix belongs to the next instruction.
            pending = (addr, data, body) if pending is None else (pending[0], pending[1] + data, pending[2] + ' ' + body)
            continue
        if pending is not None:
            addr, data, body = pending[0], pending[1] + data, pending[2] + ' ' + body
            pending = None
        rows.append([addr, data, body, []])
    if pending is not None:
        rows.append([pending[0], pending[1], pending[2], []])
    return rows


def _split_operands(text):
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
    if cur.strip():
        out.append(cur.strip())
    return out


def _memory(op):
    """(size, seg, base, index, scale, disp) of an Intel memory operand."""
    m = re.match(r'^(?:(\w+(?: \w+)?) ptr )?(?:(\w+):)?\[(.*)\]$', op)
    if not m:
        return None
    size, seg, inner = m.group(1), m.group(2), m.group(3)
    base = index = None
    scale, disp = 1, 0
    for sign, term in re.findall(r'([+-]?)\s*([^+-]+)', inner.replace(' ', '')):
        if '*' in term:
            a, b = term.split('*')
            reg, factor = (b, a) if _is_num(a) else (a, b)
            index, scale = reg, _num(factor)
        elif term in _GPR:
            if base is None:
                base = term
            else:
                index = term
        elif _is_num(term):
            disp += -_num(term) if sign == '-' else _num(term)
        else:
            return None
    return size, seg, base, index, scale, disp


def build(rows, start=None, size=None, base=None, symbols=None, candidate=False):
    """Normalised instructions of one side. `rows` from parse_listing (absolute addresses).

    `start` is the function's address in the listing's address space (default: the first row),
    `base` the image base for the target side (address minus base is the RVA), `symbols` a map of
    name -> RVA for resolving the candidate's relocations.
    """
    if not rows:
        return []
    start = rows[0][0] if start is None else start
    end = rows[-1][0] + len(rows[-1][1])
    if size is not None:
        end = start + size
    symbols = symbols or {}
    out = []
    for idx, (addr, data, text, relocs) in enumerate(rows):
        ins = Insn()
        ins.idx, ins.addr, ins.off, ins.data, ins.relocs = idx, addr, addr - start, data, relocs
        ins.label = ins.internal = ins.ref = ins.dest = None
        body = text.split(' # ')[0]
        body = re.sub(r'\s*<[^>]*>', '', body).strip()
        ins.text = text
        parts = body.split(' ', 1)
        mnem = parts[0]
        rest = parts[1] if len(parts) > 1 else ''
        # Multi-word prefixes (`lock cmpxchg`) arrive as the first words of the body.
        while mnem in PREFIXES and rest:
            nxt = rest.split(' ', 1)
            mnem = f'{mnem} {nxt[0]}'
            rest = nxt[1] if len(nxt) > 1 else ''
        ins.mnem = mnem
        reloc = relocs[0] if relocs else None
        next_ip = addr + len(data)
        shapes, regs = [], []
        ops = _split_operands(rest)
        for pos, op in enumerate(ops):
            if op in _GPR:
                canon, width = _GPR[op]
                if canon in FIXED:
                    shapes.append(('reg', canon, width))
                else:
                    shapes.append(('reg', width))
                    regs.append(canon)
                if pos == 0:
                    ins.dest = canon
                continue
            mem = _memory(op)
            if mem is not None:
                msize, seg, mbase, mindex, scale, disp = mem
                parts_shape = ['mem', msize, seg]
                for r in (mbase, mindex):
                    if r is None:
                        parts_shape.append(None)
                    else:
                        canon = _GPR[r][0]
                        if canon in FIXED:
                            parts_shape.append(canon)
                        else:
                            parts_shape.append('r')
                            regs.append(canon)
                parts_shape.append(scale if mindex else None)
                if mbase == 'rip':
                    parts_shape.append('ref')
                    if candidate:
                        ins.ref = _cand_ref(reloc, disp, symbols)
                    else:
                        ins.ref = _targ_ref(next_ip + disp, base)
                else:
                    parts_shape.append(disp)
                shapes.append(tuple(parts_shape))
                continue
            if _is_num(op):
                value = _num(op)
                if ins.is_branch or ins.is_call:
                    if candidate and reloc is not None:
                        shapes.append(('ext',))
                        ins.ref = _cand_ref(reloc, value - next_ip, symbols)
                    elif start <= value < end:
                        shapes.append(('label',))
                        ins.internal = value
                    else:
                        shapes.append(('ext',))
                        ins.ref = ('va', value) if candidate else _targ_ref(value, base)
                elif candidate and reloc is not None and reloc[1] in ('ADDR64', 'ADDR32', 'ADDR32NB'):
                    shapes.append(('imm-ref',))
                    ins.ref = _cand_ref(reloc, value, symbols)
                else:
                    shapes.append(('imm', value))
                continue
            shapes.append(('raw', op))
        ins.shape = (mnem, tuple(shapes))
        ins.regs = tuple(regs)
        ins.mask = _mask(ins)
        out.append(ins)
    by_addr = {i.addr: i.idx for i in out}
    for ins in out:
        if ins.internal is not None:
            ins.label = by_addr.get(ins.internal)
    _blocks(out)
    _mark_frame(out)
    return out


def _targ_ref(va, base):
    return ('rva', va - base) if base is not None else ('va', va)


def _cand_ref(reloc, addend, symbols):
    if reloc is None:
        return ('none',)
    name = reloc[2]
    if name in symbols:
        return ('rva', symbols[name] + addend)
    return ('sym', name, addend)


def _mask(ins):
    """Relative byte positions of the instruction's relocated fields."""
    out = set()
    for field, kind, _ in ins.relocs:
        width = 8 if kind == 'ADDR64' else 4
        out.update(range(field - ins.addr, field - ins.addr + width))
    return frozenset(out)


def same_bytes(t, c):
    """Bytes equal outside the candidate's relocated fields; the target holds resolved values there."""
    if len(t.data) != len(c.data):
        return False
    return all(a == b or k in c.mask for k, (a, b) in enumerate(zip(t.data, c.data)))


def _blocks(insns):
    leaders = {0}
    for ins in insns:
        if ins.label is not None:
            leaders.add(ins.label)
        if ins.ends_block and ins.idx + 1 < len(insns):
            leaders.add(ins.idx + 1)
    block = -1
    for ins in insns:
        if ins.idx in leaders:
            block += 1
        ins.block = block


def is_frame(ins):
    """Prologue, epilogue, register saves and restores, and the EH state slot store (set by build)."""
    return ins.frame


_NO_WRITE = {'cmp', 'test', 'push', 'bt', 'call', 'ret', 'nop', 'ucomiss', 'ucomisd', 'comiss', 'comisd'}
_SPILLS = {'mov', 'movaps', 'movups', 'movdqa'}


def _mark_frame(insns):
    """Mark frame instructions. A save stores a callee-saved register the function has not yet
    written (in address order), so it still holds the caller's value; a restore reloads a saved
    register shortly before a return. Other stack stores of callee-saved registers are locals."""
    written, saved = set(), set()
    for ins in insns:
        mnem, shapes = ins.shape
        frame = False
        if mnem in ('push', 'pop') and ins.regs:
            frame = True
            if mnem == 'push':
                saved.add(ins.regs[0])
        elif mnem in ('sub', 'add') and shapes and shapes[0][:2] == ('reg', 'rsp'):
            frame = True
        elif mnem == 'ret':
            frame = True
        elif mnem in _SPILLS and len(shapes) == 2:
            a, b = shapes
            if a[0] == 'mem' and a[3] == 'rsp' and b[0] == 'reg' and ins.regs \
                    and ins.regs[-1] in CALLEE_SAVED and ins.regs[-1] not in written:
                frame = True
                saved.add(ins.regs[-1])
            elif a[0] == 'mem' and a[3] == 'rsp' and b == ('imm', -2):
                frame = True
            elif b[0] == 'mem' and b[3] == 'rsp' and a[0] == 'reg' and ins.regs and ins.regs[0] in saved:
                frame = _before_return(insns, ins.idx)
        elif mnem == 'lea' and shapes and shapes[0][0] == 'reg' and ins.regs[:1] == ('rbp',):
            frame = True
        ins.frame = frame
        if mnem not in _NO_WRITE and shapes and shapes[0][0] == 'reg' and ins.regs and not frame:
            written.add(ins.regs[0])


def _before_return(insns, idx, reach=6):
    for nxt in insns[idx + 1:idx + 1 + reach]:
        if nxt.mnem == 'ret' or (nxt.mnem == 'jmp' and nxt.label is None):
            return True
        if nxt.is_branch or nxt.is_call:
            return False
    return False


def _related(t, c):
    if t == c:
        return True
    ht, _ = _cond(t)
    hc, _ = _cond(c)
    if ht and ht == hc:
        return True
    return any(t in fam and c in fam for fam in (_MOVES, _COMPARES, _SHIFTS))


def _cost(t, c, mapping=None):
    if t.shape == c.shape:
        cost = 0.0 if _ref_state(t, c) != 'wrong' else 0.3
        if mapping is not None and not _regs_agree(t, c, mapping):
            cost += 0.2
        return cost
    return 1.2 if _related(t.mnem, c.mnem) else 2.0


def _regs_agree(t, c, mapping):
    return len(t.regs) == len(c.regs) and all(mapping.get(a, a) == b for a, b in zip(t.regs, c.regs))


def _ref_state(t, c):
    if t.ref is None and c.ref is None:
        return 'equal'
    if t.ref is None or c.ref is None:
        return 'wrong'
    if t.ref[0] == 'rva' and c.ref[0] == 'rva':
        return 'equal' if t.ref == c.ref else 'wrong'
    return 'unknown'


def _edit_align(T, C, mapping=None):
    """[('pair', i, j) | ('del', i) | ('ins', j)] minimising the weighted edit cost.

    With a register map, same-shape pairs that break it cost a little, so that of two identical
    shapes the one holding the corresponding value is paired.
    """
    n, m = len(T), len(C)
    if n * m > 6_000_000:
        return _difflib_align(T, C)
    INF = float('inf')
    prev = [float(j) for j in range(m + 1)]
    back = bytearray((n + 1) * (m + 1))
    for j in range(1, m + 1):
        back[j] = 2
    for i in range(1, n + 1):
        cur = [INF] * (m + 1)
        cur[0] = float(i)
        back[i * (m + 1)] = 1
        ti = T[i - 1]
        for j in range(1, m + 1):
            best, how = prev[j - 1] + _cost(ti, C[j - 1], mapping), 0
            if prev[j] + 1 < best:
                best, how = prev[j] + 1, 1
            if cur[j - 1] + 1 < best:
                best, how = cur[j - 1] + 1, 2
            cur[j] = best
            back[i * (m + 1) + j] = how
        prev = cur
    ops, i, j = [], n, m
    while i or j:
        how = back[i * (m + 1) + j]
        if i and j and how == 0:
            i, j = i - 1, j - 1
            if _cost(T[i], C[j]) >= 2.0:
                ops += [('ins', j), ('del', i)]
            else:
                ops.append(('pair', i, j))
        elif i and (how == 1 or not j):
            i -= 1
            ops.append(('del', i))
        else:
            j -= 1
            ops.append(('ins', j))
    return ops[::-1]


def _difflib_align(T, C):
    import difflib
    sm = difflib.SequenceMatcher(None, [t.shape for t in T], [c.shape for c in C], autojunk=False)
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            ops += [('pair', i1 + k, j1 + k) for k in range(i2 - i1)]
        else:
            ops += [('del', i) for i in range(i1, i2)] + [('ins', j) for j in range(j1, j2)]
    return ops


def _repair_moves(T, C, ops, window=8, mapping=None):
    """Turn del/ins with identical shapes near each other into moves, and unpaired runs into moved blocks."""
    col_t, col_c = {}, {}
    for col, op in enumerate(ops):
        if op[0] == 'del':
            col_t[op[1]] = col
        elif op[0] == 'ins':
            col_c[op[1]] = col
    moved = {}
    free_c = set(col_c)
    for i in sorted(col_t):
        best = None
        for j in sorted(free_c):
            if T[i].shape == C[j].shape and abs(col_t[i] - col_c[j]) <= window:
                rank = (mapping is not None and not _regs_agree(T[i], C[j], mapping), abs(col_t[i] - col_c[j]))
                if best is None or rank < best[0]:
                    best = (rank, j)
        if best is not None:
            moved[i] = (best[1], 'local')
            free_c.discard(best[1])
    rest_t = [i for i in sorted(col_t) if i not in moved]
    rest_c = sorted(free_c)

    def runs(idx):
        out, cur = [], []
        for k in idx:
            if cur and k != cur[-1] + 1:
                out.append(cur)
                cur = []
            cur.append(k)
        if cur:
            out.append(cur)
        return [r for r in out if len(r) >= 2]

    cand_runs = runs(rest_c)
    used = set()
    for tr in sorted(runs(rest_t), key=len, reverse=True):
        best, best_pairs = None, []
        for k, cr in enumerate(cand_runs):
            if k in used:
                continue
            sub = _edit_align([T[i] for i in tr], [C[j] for j in cr])
            pairs = [(tr[o[1]], cr[o[2]]) for o in sub if o[0] == 'pair' and T[tr[o[1]]].shape == C[cr[o[2]]].shape]
            if len(pairs) >= max(2, 0.6 * max(len(tr), len(cr))) and len(pairs) > len(best_pairs):
                best, best_pairs = k, pairs
        if best is not None:
            used.add(best)
            for i, j in best_pairs:
                moved[i] = (j, 'block')
    taken = {j for j, _ in moved.values()}
    out = []
    for op in ops:
        if op[0] == 'del' and op[1] in moved:
            out.append(('move', op[1], moved[op[1]][0], moved[op[1]][1]))
        elif op[0] == 'ins' and op[1] in taken:
            continue
        else:
            out.append(op)
    return out


def _register_map(T, C, ops):
    """Greedy bijection from the most frequent register correspondences.

    Built from body instructions: which callee-saved register a frame pushes and which it stores
    to a home slot is a separate choice, scored as a prologue difference, not as renaming.
    """
    obs = Counter()
    for frame in (False, True):
        for op in ops:
            if op[0] in ('pair', 'move'):
                t, c = T[op[1]], C[op[2]]
                if (is_frame(t) or is_frame(c)) == frame and len(t.regs) == len(c.regs) \
                        and (t.shape == c.shape or t.mnem == c.mnem):
                    obs.update(zip(t.regs, c.regs))
        if obs:
            break
    mapping, used = {}, set()
    for (tr, cr), _ in sorted(obs.items(), key=lambda kv: (-kv[1], kv[0])):
        if tr in mapping or cr in used:
            continue
        mapping[tr] = cr
        used.add(cr)
    return mapping, obs


def _map_kind(mapping, obs):
    renamed = {t: c for t, c in mapping.items() if t != c}
    total = sum(obs.values())
    agree = sum(n for (t, c), n in obs.items() if mapping.get(t) == c)
    callee_only = all(t in CALLEE_SAVED and c in CALLEE_SAVED for t, c in renamed.items())
    if not renamed:
        kind = 'identity'
    elif agree == total:
        kind = 'callee-saved bijection' if callee_only else 'bijection with caller-saved'
    else:
        kind = 'callee-saved, partly inconsistent' if callee_only else 'inconsistent'
    return renamed, kind, callee_only, agree, total


def _sub_kind(t, c):
    """Class of a substitution of two non-identical instructions."""
    ht, ct = _cond(t.mnem)
    hc, cc = _cond(c.mnem)
    if ht and ht == hc:
        if ht == 'j' and _INVERSE.get(t.mnem) == c.mnem:
            return 'block-order-or-branch-polarity', 'branch'
        if frozenset((ct, cc)) in _SIGN_PAIRS:
            return 'operand-width-or-signedness', 'width'
        return 'different-instruction', 'different'
    if t.mnem != c.mnem:
        if t.mnem in _MOVES and c.mnem in _MOVES:
            return 'operand-width-or-signedness', 'width'
        if t.mnem in _SHIFTS and c.mnem in _SHIFTS:
            return 'operand-width-or-signedness', 'width'
        return 'different-instruction', 'different'
    ts, cs = t.shape[1], c.shape[1]
    if len(ts) != len(cs):
        return 'different-instruction', 'different'
    width = const = other = False
    for a, b in zip(ts, cs):
        if a == b:
            continue
        if a[0] != b[0]:
            other = True
        elif a[0] == 'reg':
            width = width or a[-1] != b[-1]
            other = other or a[1:-1] != b[1:-1]
        elif a[0] == 'mem':
            width = width or a[1] != b[1]
            const = const or a[6] != b[6]
            other = other or a[2:6] != b[2:6]
        elif a[0] == 'imm':
            const = True
        else:
            other = True
    if other:
        return 'different-instruction', 'different'
    if width:
        return 'operand-width-or-signedness', 'width'
    if const:
        return 'constant-or-displacement', 'constant'
    return 'different-instruction', 'different'


def _arg_setup(insns, ins):
    """True when `ins` writes an argument register and a call follows in its block."""
    if ins.dest not in ARG_REGS or ins.mnem not in _WRITES_FIRST:
        return False
    for nxt in insns[ins.idx + 1:]:
        if nxt.is_call:
            return True
        if nxt.ends_block:
            return False
    return False


def decode_unwind(hexstr):
    """UNWIND_INFO fields: flags, prolog size, frame register, and the codes as (offset, op, register, value)."""
    data = bytes.fromhex(hexstr)
    if len(data) < 4:
        return None
    flags, prolog, count, frame = data[0] >> 3, data[1], data[2], data[3]
    codes, k = [], 0
    raw = data[4:4 + 2 * count]
    while k + 1 < len(raw):
        off, opinfo = raw[k], raw[k + 1]
        op, info = opinfo & 0xF, opinfo >> 4
        slot = lambda n: int.from_bytes(raw[k + 2:k + 2 + 2 * n], 'little') if k + 2 * n + 1 < len(raw) else None
        if op == 0:
            codes.append((off, 'push', UNWIND_REGS[info], None))
            k += 2
        elif op == 1:
            n = 1 if info == 0 else 2
            value = slot(n)
            codes.append((off, 'alloc', None, value * 8 if info == 0 and value is not None else value))
            k += 2 + 2 * n
        elif op == 2:
            codes.append((off, 'alloc', None, info * 8 + 8))
            k += 2
        elif op == 3:
            codes.append((off, 'setfp', None, None))
            k += 2
        elif op in (4, 5):
            n = 1 if op == 4 else 2
            value = slot(n)
            codes.append((off, 'save', UNWIND_REGS[info], value * 8 if op == 4 and value is not None else value))
            k += 2 + 2 * n
        elif op in (8, 9):
            n = 1 if op == 8 else 2
            value = slot(n)
            codes.append((off, 'savexmm', f'xmm{info}', value * 16 if op == 8 and value is not None else value))
            k += 2 + 2 * n
        else:
            codes.append((off, f'op{op}', None, info))
            k += 2
    return {'flags': flags, 'prolog': prolog, 'frame': (frame & 0xF, frame >> 4), 'codes': codes}


def compare_unwind(t_hex, c_hex, mapping):
    """(differing fields, explained by renaming) for two unwind infos."""
    t, c = decode_unwind(t_hex), decode_unwind(c_hex)
    if t is None or c is None:
        return [], False
    inverse = {cr: tr for tr, cr in mapping.items()}
    fields = []
    if t['flags'] != c['flags']:
        fields.append('flags (handler)')
    if t['frame'] != c['frame']:
        fields.append('frame register')
    if t['prolog'] != c['prolog'] or [x[0] for x in t['codes']] != [x[0] for x in c['codes']]:
        fields.append('prologue size or code offsets')
    t_alloc = [x[3] for x in t['codes'] if x[1] == 'alloc']
    c_alloc = [x[3] for x in c['codes'] if x[1] == 'alloc']
    if t_alloc != c_alloc:
        fields.append('frame size')
    t_regs = [(x[1], x[2], x[3] if x[1] != 'push' else None) for x in t['codes'] if x[2]]
    c_raw = [(x[1], x[2], x[3] if x[1] != 'push' else None) for x in c['codes'] if x[2]]
    c_regs = [(op, inverse.get(r, r), v) for op, r, v in c_raw]
    explained = False
    if t_regs != c_regs:
        fields.append('saved register set or order')
    elif t_regs != c_raw:
        explained = True
    return fields, explained


class Diff:
    __slots__ = ('cls', 'weight', 'component', 't', 'c')

    def __init__(self, cls, weight, component, t=None, c=None):
        self.cls, self.weight, self.component, self.t, self.c = cls, weight, component, t, c


def analyse(T, C, unwind=None):
    """Alignment, register map, differences and distance for two normalised instruction lists."""
    ops = _repair_moves(T, C, _edit_align(T, C))
    mapping, obs = _register_map(T, C, ops)
    for _ in range(2):
        ops = _repair_moves(T, C, _edit_align(T, C, mapping), mapping=mapping)
        again, obs = _register_map(T, C, ops)
        if again == mapping:
            break
        mapping = again
    renamed, kind, callee_only, agree, total = _map_kind(mapping, obs)
    t_of_c = {}
    for op in ops:
        if op[0] in ('pair', 'move'):
            t_of_c[op[2]] = op[1]
    paired_t = sorted(set(t_of_c.values()))
    paired_c = sorted(t_of_c)

    def same_label(lt, lc):
        """Branch targets correspond when the first paired instruction at or after each label is a pair.

        Anchoring on the next paired instruction keeps one missing instruction at a label from
        also counting as a branch difference at every jump to it.
        """
        a = bisect.bisect_left(paired_t, lt)
        b = bisect.bisect_left(paired_c, lc)
        if a == len(paired_t) or b == len(paired_c):
            return a == len(paired_t) and b == len(paired_c)
        return t_of_c[paired_c[b]] == paired_t[a]
    diffs, rows, frame_mismatch = [], [], []

    def comp(*insns):
        return 'prologue' if any(i is not None and is_frame(i) for i in insns) else 'body'

    for op in ops:
        if op[0] == 'del':
            t = T[op[1]]
            if is_frame(t):
                d = Diff('prologue-or-unwind', WEIGHT['missing'], 'prologue', t=t)
            elif t.is_call or _arg_setup(T, t):
                d = Diff('callee-or-argument-setup', WEIGHT['missing'], 'refs' if t.is_call else 'body', t=t)
            else:
                d = Diff('missing-instruction', WEIGHT['missing'], 'body', t=t)
            diffs.append(d)
            rows.append(('-', t, None, [d.cls]))
            continue
        if op[0] == 'ins':
            c = C[op[1]]
            if is_frame(c):
                d = Diff('prologue-or-unwind', WEIGHT['extra'], 'prologue', c=c)
            elif c.is_call or _arg_setup(C, c):
                d = Diff('callee-or-argument-setup', WEIGHT['extra'], 'refs' if c.is_call else 'body', c=c)
            else:
                d = Diff('extra-instruction', WEIGHT['extra'], 'body', c=c)
            diffs.append(d)
            rows.append(('+', None, c, [d.cls]))
            continue
        t, c = T[op[1]], C[op[2]]
        here = []
        if op[0] == 'move':
            cls = 'block-order-or-branch-polarity' if op[3] == 'block' or t.is_branch else 'reordered-instructions'
            if is_frame(t):
                cls = 'prologue-or-unwind'
            here.append(Diff(cls, WEIGHT['moved'], comp(t, c), t, c))
        if t.shape != c.shape:
            cls, w = _sub_kind(t, c)
            component = comp(t, c)
            if component == 'prologue':
                cls = 'prologue-or-unwind'
            elif t.is_call and c.is_call:
                cls, component = 'callee-or-argument-setup', 'refs'
            elif cls in ('different-instruction', 'operand-width-or-signedness', 'constant-or-displacement') \
                    and (_arg_setup(T, t) or _arg_setup(C, c)):
                cls = 'callee-or-argument-setup'
            here.append(Diff(cls, WEIGHT[w], component, t, c))
        else:
            state = _ref_state(t, c)
            if state == 'wrong':
                cls = 'callee-or-argument-setup' if t.is_call or (t.is_branch and not t.is_jcc) else 'reference-target'
                here.append(Diff(cls, WEIGHT['wrong-ref'], 'refs', t, c))
            elif state == 'unknown':
                here.append(Diff('reference-target', WEIGHT['unresolved-ref'], 'refs', t, c))
            if t.label is not None and c.label is not None and not same_label(t.label, c.label):
                here.append(Diff('block-order-or-branch-polarity', WEIGHT['branch'], 'body', t, c))
        regs_ok = _regs_agree(t, c, mapping)
        if t.shape == c.shape and not regs_ok:
            if is_frame(t) and is_frame(c):
                frame_mismatch.append((t, c))
                here.append(Diff('prologue-or-unwind', 0.0, 'prologue', t, c))
            else:
                here.append(Diff('register-renaming', WEIGHT['inconsistent-reg'], comp(t, c), t, c))
        if not here and not same_bytes(t, c) and t.label is None and not any(a != b for a, b in zip(t.regs, c.regs)):
            here.append(Diff('encoding', WEIGHT['encoding'], comp(t, c), t, c))
        renamed_only = not here and t.regs != c.regs
        diffs += here
        mark = ('m' if op[0] == 'move' else '~' if t.shape != c.shape else '!') if here else ('r' if renamed_only else ' ')
        rows.append((mark, t, c, [d.cls for d in here] + (['register-renaming'] if renamed_only else [])))

    if frame_mismatch:
        # Saved registers compared as sets through the map: the same set in another push/home-slot
        # order is one difference; each register saved on one side only is one more.
        inverse = {cr: tr for tr, cr in mapping.items()}
        t_saved = {r for i in T if is_frame(i) for r in i.regs if r in CALLEE_SAVED}
        c_saved = {inverse.get(r, r) for i in C if is_frame(i) for r in i.regs if r in CALLEE_SAVED}
        diffs.append(Diff('prologue-or-unwind', WEIGHT['unwind-field'], 'prologue'))
        for _ in t_saved ^ c_saved:
            diffs.append(Diff('prologue-or-unwind', WEIGHT['unwind-field'], 'prologue'))
    for tr, cr in renamed.items():
        w = WEIGHT['rename-callee-saved'] if tr in CALLEE_SAVED and cr in CALLEE_SAVED else WEIGHT['rename-volatile']
        diffs.append(Diff('register-renaming', w, 'body'))
    unwind_fields, unwind_explained = [], False
    if unwind and unwind[0] and unwind[1]:
        unwind_fields, unwind_explained = compare_unwind(unwind[0], unwind[1], mapping)
        for _ in unwind_fields:
            diffs.append(Diff('prologue-or-unwind', WEIGHT['unwind-field'], 'prologue'))

    exact = (len(T) == len(C) and all(op[0] == 'pair' and op[1] == op[2] for op in ops)
             and all(same_bytes(T[op[1]], C[op[2]]) and _ref_state(T[op[1]], C[op[2]]) == 'equal' for op in ops)
             and not unwind_fields and not (unwind and unwind[0] and unwind[1] and unwind[0] != unwind[1]))
    if not exact and not diffs:
        # Bytes differ somewhere the normalisation cannot name (an encoding or branch form).
        for mark, t, c, _ in rows:
            if t is not None and c is not None and not same_bytes(t, c):
                diffs.append(Diff('encoding', WEIGHT['encoding'], 'body', t, c))
        if not diffs:
            diffs.append(Diff('encoding', WEIGHT['encoding'], 'body'))
    components = {'prologue': 0.0, 'body': 0.0, 'refs': 0.0}
    for d in diffs:
        components[d.component] += d.weight
    components = {k: round(v, 2) for k, v in components.items()}
    distance = 0.0 if exact else round(sum(components.values()), 2)
    shape_edits = sum(1 for o in ops if o[0] in ('del', 'ins')) \
        + sum(2 if o[0] == 'move' else 1 for o in ops if o[0] in ('pair', 'move')
              and (o[0] == 'move' or T[o[1]].shape != C[o[2]].shape
                   or (T[o[1]].label is not None and C[o[2]].label is not None
                       and not same_label(T[o[1]].label, C[o[2]].label))))
    exact_edits = shape_edits + sum(1 for o in ops if o[0] == 'pair' and T[o[1]].shape == C[o[2]].shape
                                    and (not same_bytes(T[o[1]], C[o[2]]) or T[o[1]].regs != C[o[2]].regs))
    return {
        'ops': ops, 'rows': rows, 'diffs': diffs, 'mapping': mapping, 'renamed': renamed, 'map_kind': kind,
        'map_agree': agree, 'map_total': total, 'unwind_fields': unwind_fields,
        'unwind_explained': unwind_explained, 'exact': exact, 'distance': distance,
        'components': components, 'shape_edits': shape_edits, 'exact_edits': exact_edits,
    }


def _hunks(rows):
    hunks, cur = [], None
    for mark, t, c, classes in rows:
        if mark in (' ', 'r'):
            cur = None
            continue
        if cur is None:
            cur = {'t': [None, None], 'c': [None, None], 'classes': Counter()}
            hunks.append(cur)
        for side, ins in (('t', t), ('c', c)):
            if ins is not None:
                lo, hi = cur[side]
                cur[side] = [ins.off if lo is None else min(lo, ins.off), ins.off if hi is None else max(hi, ins.off)]
        cur['classes'].update(classes)
    return hunks


def _rules(T, C, result, counts):
    """Cookbook rule ids whose symptom the differences show."""
    rules = []
    only = set(counts) - {'register-renaming'}
    # Same instructions (as a multiset of normalised forms) with callee-saved registers exchanged
    # consistently: scheduling may differ because it follows the register choice.
    if result['renamed'] and result['map_kind'] == 'callee-saved bijection' \
            and Counter(i.shape for i in T) == Counter(i.shape for i in C) \
            and not (only - {'prologue-or-unwind', 'encoding', 'reordered-instructions'}):
        rules.append(12)
    t_only = [r[1] for r in result['rows'] if r[0] == '-']
    c_only = [r[2] for r in result['rows'] if r[0] == '+']
    if any(t.mnem == 'test' and t.regs[:1] == t.regs[1:2] and i + 1 < len(T) and T[t.idx + 1].is_jcc
           for i, t in enumerate(t_only)):
        rules.append(1)
    if counts.get('block-order-or-branch-polarity', 0) >= 1 and any(
            d.cls == 'block-order-or-branch-polarity' for d in result['diffs']):
        rules.append(2)
    if counts.get('reordered-instructions'):
        rules.append(4)
    # The target repeats work the candidate does once: two or more missing instructions that
    # duplicate instructions the candidate does have (an inlined helper called twice).
    paired_shapes = {r[1].shape for r in result['rows'] if r[1] is not None and r[2] is not None}
    if sum(t.shape in paired_shapes and not t.is_branch for t in t_only) >= 2:
        rules.append(3)
    if counts.get('callee-or-argument-setup') and not t_only + c_only or \
            any(d.cls == 'callee-or-argument-setup' and d.component == 'body' for d in result['diffs']):
        rules.append(5)
    if counts.get('operand-width-or-signedness'):
        rules.append(6)
    if any(t.shape[1][-1:] == (('imm', -1),) for t in t_only) or any(
            t.mnem == 'or' and t.shape[1][-1:] == (('imm', -1),) for t in t_only):
        rules.append(7)
    if any(c.mnem == 'mov' and c.shape[1] and c.shape[1][0][0] == 'mem' and c.shape[1][0][3] == 'rsp'
           and (c.shape[1][-1] == ('imm', 0) or _zeroed(C, c)) for c in c_only):
        rules.append(9)
    calls_t, calls_c = sum(i.is_call for i in T), sum(i.is_call for i in C)
    if calls_c > calls_t and any(i.mnem == 'mov' and i.dest == 'rdx' and i.shape[1][-1] == ('imm', 1) for i in T):
        rules.append(10)
    if any(d.cls == 'constant-or-displacement' and d.t is not None and d.t.is_call for d in result['diffs']):
        rules.append(11)
    eh_slot = {t.shape for t in T if t.frame and t.shape[1][-1:] == (('imm', -2),)}
    if eh_slot and not eh_slot & {c.shape for c in C}:
        rules.append(13)
    if 'flags (handler)' in result['unwind_fields']:
        rules.append(13)
    return sorted(set(rules), key=RULE_PRIORITY.index)


def _zeroed(insns, ins):
    """True when the stored register's last write before `ins` (address order) was `xor r, r`.

    Epilogue restores are skipped: they sit on other paths that return before `ins`.
    """
    if ins.shape[1][-1][0] != 'reg' or not ins.regs:
        return False
    reg = ins.regs[-1]
    for prev in reversed(insns[:ins.idx]):
        if prev.regs[:1] == (reg,) and prev.shape[1] and prev.shape[1][0][0] == 'reg' and prev.mnem not in _NO_WRITE \
                and not prev.frame:
            return prev.mnem == 'xor' and prev.regs[1:2] == (reg,)
    return False


SUGGEST = {
    'register-renaming': 'value lifetimes differ: change declaration order, name or inline a temporary (cookbook 4)',
    'missing-instruction': 'the target does work the candidate skips: a re-read member, a repeated test or a helper called twice (cookbook 1, 3)',
    'extra-instruction': 'the candidate does work the target skips: an initialiser, a cached value or a redundant test (cookbook 9)',
    'operand-width-or-signedness': 'change the width or signedness of a local, parameter or switch operand (cookbook 6)',
    'reordered-instructions': 'put the loads and computations in the target\'s source order (cookbook 4)',
    'block-order-or-branch-polarity': 'invert or reorder the condition, early return versus else (cookbook 2, 8)',
    'prologue-or-unwind': 'the frame differs: locals, saved registers or an EH object (cookbook 13 if a -2 store)',
    'callee-or-argument-setup': 'check the callee declaration: arity, widths and the bound symbol (cookbook 5, 10)',
    'constant-or-displacement': 'a field offset, vtable slot or constant differs: check the layout (cookbook 11)',
    'reference-target': 'a reference resolves elsewhere or is unbound: check bindings and the global used',
    'different-instruction': 'an expression is computed differently: try the operator form or operand order',
    'encoding': 'only encodings differ: look at the first differing row in the aligned listing',
}


def report(T, C, unwind=None):
    """(summary lines, JSON dict, aligned listing text) for two normalised instruction lists."""
    result = analyse(T, C, unwind)
    counts, costs = Counter(), Counter()
    for d in result['diffs']:
        counts[d.cls] += 1
        costs[d.cls] += d.weight
    hunks = _hunks(result['rows'])
    rules = _rules(T, C, result, counts)
    comps = result['components']
    lines = [f'aligned: distance {result["distance"]:g} (prologue {comps["prologue"]:g}, body {comps["body"]:g}, '
             f'refs {comps["refs"]:g}); edits shape {result["shape_edits"]}, exact {result["exact_edits"]} '
             f'of {len(T)} target instructions ({len(C)} candidate)']
    if result['exact']:
        lines.append('aligned: identical instructions outside relocated fields')
    if result['renamed']:
        pairs = ', '.join(f'{t}->{c}' for t, c in sorted(result['renamed'].items()))
        lines.append(f'registers: {result["map_kind"]} ({pairs}); '
                     f'{result["map_agree"]}/{result["map_total"]} uses agree')
    if counts:
        top = sorted(counts, key=lambda k: (-costs[k], k))
        lines.append('classes: ' + ', '.join(f'{k} {counts[k]} ({costs[k]:g})' for k in top[:6]))
    shown = [h for h in hunks if set(h['classes']) - {'register-renaming'}][:4]
    if shown:
        def span(h):
            lo, hi = h['t'] if h['t'][0] is not None else h['c']
            side = '' if h['t'][0] is not None else 'candidate '
            return side + (f'+{lo:#x}' if lo == hi else f'+{lo:#x}..+{hi:#x}')
        lines.append('hunks (target offsets): ' + '; '.join(
            f'{span(h)} {h["classes"].most_common(1)[0][0]}' for h in shown)
            + (f'; {len(hunks) - len(shown)} more' if len(hunks) > len(shown) else ''))
    if result['unwind_fields'] or result['unwind_explained']:
        lines.append('unwind: ' + (', '.join(result['unwind_fields']) if result['unwind_fields'] else 'differs')
                     + ('' if result['unwind_fields'] else ' only by the register map'))
    if rules:
        lines.append('cookbook: ' + '; '.join(f'{r} {COOKBOOK[r]}' for r in rules[:3]))
    suggestion = None
    if rules:
        suggestion = f'{COOKBOOK[rules[0]]} (cookbook {rules[0]})'
    elif counts:
        main = max((k for k in counts if k != 'register-renaming' or len(counts) == 1),
                   key=lambda k: (costs[k], k), default=None)
        suggestion = SUGGEST.get(main) if main else None
    if suggestion:
        lines.append(f'next: {suggestion}')
    data = {
        'schema': SCHEMA, 'distance': result['distance'], 'components': comps, 'exact': result['exact'],
        'edits': {'shape': result['shape_edits'], 'exact': result['exact_edits']},
        'target_instructions': len(T), 'candidate_instructions': len(C),
        'register_map': {'kind': result['map_kind'], 'renamed': dict(sorted(result['renamed'].items())),
                         'uses_agree': result['map_agree'], 'uses': result['map_total']},
        'classes': {k: {'count': counts[k], 'cost': round(costs[k], 2)} for k in sorted(counts)},
        'hunks': [{'target': h['t'], 'candidate': h['c'], 'classes': dict(h['classes'])} for h in hunks],
        'unwind': {'fields': result['unwind_fields'], 'explained_by_register_map': result['unwind_explained']},
        'cookbook_rules': rules, 'suggestion': suggestion,
        'alignment': [_op_json(op, T, C) for op in result['ops']],
    }
    return lines, data, _listing(result, T, C, lines)


def _op_json(op, T, C):
    if op[0] == 'del':
        return {'op': 'missing', 't': T[op[1]].off}
    if op[0] == 'ins':
        return {'op': 'extra', 'c': C[op[1]].off}
    return {'op': 'moved' if op[0] == 'move' else 'pair', 't': T[op[1]].off, 'c': C[op[2]].off}


def _listing(result, T, C, lines, width=56):
    out = ['# Private aligned listing (game-derived; never paste or commit). Marks: " " equal, r registers',
           '# renamed per the map, ! same shape but differs, ~ substituted, m moved, - target only, + candidate only.']
    out += [f'# {line}' for line in lines]
    out.append(f'  {"off":>5}  {"target":<{width}}  {"off":>5}  {"candidate":<{width}}  class')
    for mark, t, c, classes in result['rows']:
        left = f'{t.off:>5x}  {t.text[:width]:<{width}}' if t else f'{"":>5}  {"":<{width}}'
        right = f'{c.off:>5x}  {c.text[:width]:<{width}}' if c else f'{"":>5}  {"":<{width}}'
        out.append(f'{mark} {left}  {right}  {",".join(classes)}'.rstrip())
    return '\n'.join(out) + '\n'


def _as_rows(listing):
    if isinstance(listing, str):
        return parse_listing(listing)
    return [[r[0], r[1].split() if isinstance(r[1], str) else list(r[1]), r[2],
             list(r[3]) if len(r) > 3 else []] for r in listing]


def load_symbols(path):
    """name -> RVA from a task symbol map ({"symbols": {name: {"rva": n}}} or {name: n})."""
    if path is None or not Path(path).is_file():
        return {}
    raw = json.loads(Path(path).read_text())
    raw = raw.get('symbols', raw) if isinstance(raw, dict) else {}
    out = {}
    for name, value in raw.items():
        rva = value.get('rva') if isinstance(value, dict) else value
        if isinstance(rva, int):
            out[name] = rva
    return out


def summarise(target_listing, candidate_listing, symbols=None, target_rva=None, image_base=None,
              target_size=None, unwind=None, listing_path=None):
    """(summary text, JSON dict) for one function.

    Listings are llvm-objdump text (the candidate with -r) or rows of (address, bytes, text,
    relocations). `symbols` maps candidate symbol names to RVAs; with `target_rva` or
    `image_base` the target's references become RVAs and can be checked against them. `unwind` is
    (target hex, candidate hex) of the two UNWIND_INFO blocks when known. When `listing_path` is
    given the full aligned listing is written there (private).
    """
    t_rows, c_rows = _as_rows(target_listing), _as_rows(candidate_listing)
    if image_base is None and target_rva is not None and t_rows:
        image_base = t_rows[0][0] - target_rva
    T = build(t_rows, size=target_size, base=image_base)
    C = build(c_rows, symbols=symbols if isinstance(symbols, dict) else load_symbols(symbols), candidate=True)
    lines, data, listing = report(T, C, unwind)
    if listing_path is not None:
        Path(listing_path).write_text(listing)
    return '\n'.join(lines), data


def objdump_target(objdump, image, rva, size):
    base = disasm.image_base(image)
    out = subprocess.run([objdump, '-d', '--x86-asm-syntax=intel', f'--start-address=0x{base + rva:x}',
                          f'--stop-address=0x{base + rva + size:x}', str(image)],
                         capture_output=True, text=True, timeout=120)
    return out.stdout, base


def objdump_candidate(objdump, obj, symbol):
    out = subprocess.run([objdump, '-d', '-r', '--x86-asm-syntax=intel', f'--disassemble-symbols={symbol}', str(obj)],
                         capture_output=True, text=True, timeout=120)
    return out.stdout


def unwind_from_diagnostics(fdir):
    """(target hex, candidate hex) when the comparator's private diagnostics hold the two unwind infos."""
    try:
        diag = json.loads((Path(fdir) / 'diagnostics.json').read_text())
    except (OSError, ValueError):
        return None
    raw = diag.get('raw') if isinstance(diag, dict) else None
    reason = (diag.get('report') or {}).get('reason') if isinstance(diag, dict) else None
    if reason == 'unwind-info-mismatch' and isinstance(raw, dict) \
            and isinstance(raw.get('target'), str) and isinstance(raw.get('candidate'), str):
        return raw['target'], raw['candidate']
    return None


def align_function(fdir, objdump, image, obj, symbol, rva, size, symbols=None, unwind=None, out_dir=None):
    """Align one compiled function against the image; writes align.txt and align.json to `out_dir`.

    `fdir` is the attempt's function directory (its diagnostics.json supplies the unwind infos);
    `out_dir` defaults to it.
    """
    target, base = objdump_target(objdump, image, rva, size)
    candidate = objdump_candidate(objdump, obj, symbol)
    if not parse_listing(candidate):
        raise ValueError('candidate object does not disassemble the function symbol')
    if unwind is None:
        unwind = unwind_from_diagnostics(fdir)
    out = Path(out_dir) if out_dir is not None else Path(fdir)
    out.mkdir(parents=True, exist_ok=True)
    text, data = summarise(target, candidate, symbols=symbols, image_base=base, target_size=size, unwind=unwind,
                           listing_path=out / 'align.txt')
    (out / 'align.json').write_text(json.dumps(data, indent=1) + '\n')
    return text, data


def attempt_summary(fdir, objdump, image, obj, fn, symbols_path=None):
    """Lines for `attempt` under a failing function's line; never raises."""
    try:
        if objdump is None or image is None or not Path(image).is_file() or not Path(obj).is_file():
            return ['aligned: not available (no objdump, image or candidate object)']
        text, _ = align_function(fdir, objdump, image, obj, fn['symbol'], fn['rva'], fn['size'],
                                 symbols=load_symbols(symbols_path))
        return text.splitlines() + [f'aligned listing: {Path(fdir) / "align.txt"}']
    except Exception as exc:  # noqa: BLE001 - a broken diagnostic must not hide the comparator's result
        return [f'aligned: not available ({type(exc).__name__}: {exc})']


def _config_image():
    try:
        repo = Path(__file__).resolve().parents[2]
        config = json.loads((repo / '.local' / 'verifier' / 'config.json').read_text())
        return config.get('image'), config.get('objdump')
    except (OSError, ValueError):
        return None, None


def run_attempt_dir(attempt_dir, task_dir=None, image=None, objdump=None, include_passes=False, out_root=None):
    """Align every function of one stored attempt; yields (rva, reason, summary text, data).

    Outputs go next to each function's diagnostics, or under `out_root/<rva>/` when given (for
    reading another checkout's attempts without writing there).
    """
    attempt_dir = Path(attempt_dir)
    task_dir = Path(task_dir) if task_dir else attempt_dir.parent.parent
    symbols = load_symbols(task_dir / 'symbols.json')
    for fdir in sorted(p for p in attempt_dir.glob('0x*') if p.is_dir()):
        try:
            rep = json.loads((fdir / 'report.json').read_text())
        except (OSError, ValueError):
            continue
        fn = rep.get('function') or {}
        if not include_passes and rep.get('result') == 'pass':
            continue
        if not fn.get('symbol') or not (attempt_dir / 'candidate.obj').is_file():
            continue
        try:
            text, data = align_function(fdir, objdump, image, attempt_dir / 'candidate.obj', fn['symbol'],
                                        fn['rva'], fn['size'], symbols=symbols,
                                        out_dir=Path(out_root) / fdir.name if out_root else None)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            yield fn.get('rva'), rep.get('reason'), f'aligned: not available ({exc})', None
            continue
        yield fn['rva'], rep.get('reason'), text, data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--attempt', help='a stored attempt directory (<task-dir>/attempts/NNN)')
    p.add_argument('--task-dir', help='task directory holding symbols.json (default: two levels up from --attempt)')
    p.add_argument('--all', action='store_true', help='with --attempt: passing functions too')
    p.add_argument('--target', help='target listing file (llvm-objdump text)')
    p.add_argument('--candidate', help='candidate listing file (llvm-objdump -r text)')
    p.add_argument('--object', help='candidate object')
    p.add_argument('--symbol', help='candidate function symbol')
    p.add_argument('--rva', type=lambda s: int(s, 0))
    p.add_argument('--size', type=lambda s: int(s, 0))
    p.add_argument('--image-base', type=lambda s: int(s, 0))
    p.add_argument('--symbols', help='task symbol map (symbols.json)')
    p.add_argument('--image', help='pinned image (default: .local/verifier/config.json)')
    p.add_argument('--objdump', help='llvm-objdump (default: as disasm.py finds it)')
    p.add_argument('--out', help='directory for align.txt and align.json (with --attempt: one subdirectory per function)')
    p.add_argument('--json', action='store_true', help='print the JSON instead of the summary')
    a = p.parse_args(argv)
    image, configured = _config_image()
    image = a.image or image
    objdump = disasm.find_objdump(a.objdump or configured or os.environ.get('SR_OBJDUMP'))
    if a.attempt:
        for rva, reason, text, data in run_attempt_dir(a.attempt, a.task_dir, image, objdump, a.all, a.out):
            print(f'0x{rva:x} {reason}')
            print(json.dumps(data, indent=1) if a.json and data else '\n'.join('    ' + s for s in text.splitlines()))
        return 0
    if a.target and a.candidate:
        listing = Path(a.out) / 'align.txt' if a.out else None
        text, data = summarise(Path(a.target).read_text(), Path(a.candidate).read_text(), symbols=a.symbols,
                               target_rva=a.rva, image_base=a.image_base, target_size=a.size, listing_path=listing)
        if a.out:
            (Path(a.out) / 'align.json').write_text(json.dumps(data, indent=1) + '\n')
        print(json.dumps(data, indent=1) if a.json else text)
        return 0
    if a.object and a.symbol and a.rva is not None and a.size:
        if objdump is None or image is None:
            p.error('needs llvm-objdump and the local image')
        out = Path(a.out) if a.out else Path(a.object).parent
        text, data = align_function(out, objdump, image, a.object, a.symbol, a.rva, a.size,
                                    symbols=load_symbols(a.symbols))
        print(json.dumps(data, indent=1) if a.json else text)
        return 0
    p.error('give --attempt, or --target and --candidate, or --object, --symbol, --rva and --size')


if __name__ == '__main__':
    raise SystemExit(main())
