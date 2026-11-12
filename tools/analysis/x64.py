"""Minimal x86-64 instruction length decoder for clustering and census work on the pinned image.

It finds instruction boundaries and the fields a linker would patch when the code comes from an
MSVC object: branch displacements (`REL32`), RIP-relative displacements (`REL32` or `REL32_k`
with `k` immediate bytes after the field) and displacements based on a register that holds the
image base (`ADDR32NB`, the switch-table form). Those are the fields `tools/compare.py` compares
as references; every other byte it compares exactly, so the same split is used here. It also
yields a register-abstracted key per instruction for the inlined-body census.

The decoder covers the general-purpose, x87, SSE and VEX/EVEX encodings MSVC emits. It is a
reading aid, not a disassembler: `tests/test_analysis_x64.py` checks it on original synthetic
encodings; `findings/clusters-and-inlined-helpers.md` reports a cross-check of boundaries and
targets against llvm-objdump on the pinned image. A byte sequence it cannot decode raises `DecodeError`, so callers can fail closed.
"""

LEGACY = frozenset((0xF0, 0xF2, 0xF3, 0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65, 0x66, 0x67))

# One-byte opcodes with a ModRM byte (0xC4/0xC5/0x62 are VEX/EVEX in 64-bit mode, handled apart).
MODRM1 = set()
for _base in range(0x00, 0x40, 8):
    MODRM1.update(range(_base, _base + 4))
MODRM1.update((0x63, 0x69, 0x6B, 0xC0, 0xC1, 0xC6, 0xC7, 0xD0, 0xD1, 0xD2, 0xD3, 0xF6, 0xF7, 0xFE, 0xFF))
MODRM1.update(range(0x80, 0x90))
MODRM1.update(range(0xD8, 0xE0))
MODRM1 = frozenset(MODRM1)

IMM8_1 = frozenset((0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x34, 0x3C, 0x6A, 0x6B, 0x80, 0x83, 0xA8, 0xC0,
                    0xC1, 0xC6, 0xCD, 0xE4, 0xE5, 0xE6, 0xE7) + tuple(range(0xB0, 0xB8)))
IMMZ_1 = frozenset((0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x35, 0x3D, 0x68, 0x69, 0x81, 0xA9, 0xC7))
REL8_1 = frozenset(tuple(range(0x70, 0x80)) + (0xE0, 0xE1, 0xE2, 0xE3, 0xEB))
INVALID_1 = frozenset((0x06, 0x07, 0x0E, 0x16, 0x17, 0x1E, 0x1F, 0x27, 0x2F, 0x37, 0x3F, 0x60, 0x61, 0x82,
                       0x9A, 0xCE, 0xD4, 0xD5, 0xD6, 0xEA))
# Opcodes whose ModRM reg field selects the operation rather than a register.
GROUP1 = frozenset((0x80, 0x81, 0x83, 0x8F, 0xC0, 0xC1, 0xC6, 0xC7, 0xD0, 0xD1, 0xD2, 0xD3, 0xF6, 0xF7,
                    0xFE, 0xFF) + tuple(range(0xD8, 0xE0)))
REG_IN_OPCODE1 = frozenset(tuple(range(0x50, 0x60)) + tuple(range(0x91, 0x98)) + tuple(range(0xB0, 0xC0)))

NO_MODRM_0F = frozenset((0x05, 0x06, 0x07, 0x08, 0x09, 0x0B, 0x0E, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35,
                         0x37, 0x77, 0xA0, 0xA1, 0xA2, 0xA8, 0xA9, 0xAA) + tuple(range(0xC8, 0xD0)))
IMM8_0F = frozenset((0x70, 0x71, 0x72, 0x73, 0xA4, 0xAC, 0xBA, 0xC2, 0xC4, 0xC5, 0xC6))
GROUP_0F = frozenset((0x00, 0x01, 0x18, 0x0D, 0x71, 0x72, 0x73, 0xAE, 0xBA, 0xC7))

# Flow classes.
OTHER, CALL, JMP, JCC, RET, INT3, ICALL, IJMP, NOP = range(9)


class DecodeError(ValueError):
    pass


class Insn:
    """One decoded instruction. Offsets are relative to the instruction start.

    `rel` is (offset, size) of a branch displacement; `target` its absolute destination.
    `rip` is the offset of a RIP-relative disp32; `rip_target` the address it reaches.
    `disp` is (offset, size, value) of any other memory displacement; `base`/`index` are the
    full register numbers (0-15) of the memory operand or None; `reg` is the ModRM reg field
    with REX.R (a register operand, or the opcode extension for group opcodes).
    `imm` is (offset, size) of the immediate operand.
    `key` is a bytes value with register numbers removed and reference fields left out, for the
    census; the caller appends reference identities as it sees fit.
    """
    __slots__ = ('length', 'flow', 'rel', 'target', 'rip', 'rip_target', 'disp', 'base', 'index',
                 'reg', 'key', 'opcode', 'lea', 'imm')

    def __init__(self):
        self.rel = self.target = self.rip = self.rip_target = self.disp = None
        self.base = self.index = self.reg = self.imm = None
        self.flow = OTHER
        self.lea = False


def _modrm(buf, p, end, rex_b, rex_x):
    """(position after ModRM/SIB/disp, mod, rm, base, index, scale, disp tuple or None, rip, key byte list)."""
    if p >= end:
        raise DecodeError('truncated modrm')
    m = buf[p]
    mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
    p += 1
    base = index = None
    scale = 0
    disp = None
    rip = False
    key = []
    if mod == 3:
        key.append(0xC0)
        return p, mod, rm, None, None, 0, None, False, key
    if rm == 4:
        if p >= end:
            raise DecodeError('truncated sib')
        s = buf[p]
        p += 1
        scale, idx, b = s >> 6, (s >> 3) & 7, s & 7
        index = None if (idx == 4 and not rex_x) else idx | (rex_x << 3)
        if b == 5 and mod == 0:
            base = None
            dsize = 4
        else:
            base = b | (rex_b << 3)
            dsize = 1 if mod == 1 else 4 if mod == 2 else 0
        key.extend((mod << 6 | 4, scale << 6 | (0 if index is None else 8) | (7 if base is None else 4 if base == 4 else 5 if base == 5 and mod else 0)))
    elif rm == 5 and mod == 0:
        rip = True
        dsize = 4
        key.append(0x05)
    else:
        base = rm | (rex_b << 3)
        dsize = 1 if mod == 1 else 4 if mod == 2 else 0
        key.append(mod << 6 | (4 if base == 4 else 5 if base == 5 else 0))
    if dsize:
        if p + dsize > end:
            raise DecodeError('truncated displacement')
        raw = buf[p:p + dsize]
        value = int.from_bytes(raw, 'little', signed=True)
        disp = (p, dsize, value)
        p += dsize
    return p, mod, rm, base, index, scale, disp, rip, key


def decode(buf, pos, ip, end=None):
    """Decode the instruction at buf[pos]; `ip` is its address (any base), used for targets."""
    if end is None:
        end = len(buf)
    start = pos
    p = pos
    opsize = addrsize = False
    rep = 0
    while p < end and buf[p] in LEGACY:
        b = buf[p]
        if b == 0x66:
            opsize = True
        elif b == 0x67:
            addrsize = True
        elif b in (0xF2, 0xF3):
            rep = b
        p += 1
        if p - start > 14:
            raise DecodeError('too many prefixes')
    if p >= end:
        raise DecodeError('truncated')
    prefix_key = bytes(buf[start:p])
    rex = 0
    if 0x40 <= buf[p] <= 0x4F:
        rex = buf[p]
        p += 1
        if p >= end:
            raise DecodeError('truncated after rex')
    rex_w, rex_r, rex_x, rex_b = (rex >> 3) & 1, (rex >> 2) & 1, (rex >> 1) & 1, rex & 1
    ins = Insn()
    op = buf[p]
    p += 1
    has_modrm = False
    imm = 0
    rel = 0
    group = False
    vex_map = None
    key_head = bytearray(prefix_key)
    if rex:
        key_head.append(0x40 | rex_w << 3)
    if op in (0xC4, 0xC5, 0x62):
        if op == 0xC5:
            if p >= end:
                raise DecodeError('truncated vex')
            v = buf[p]
            rex_r = 1 - (v >> 7)
            vex_map = 1
            key_head.extend((0xC5, v & 0x07))
            p += 1
        elif op == 0xC4:
            if p + 1 >= end:
                raise DecodeError('truncated vex')
            v1, v2 = buf[p], buf[p + 1]
            rex_r, rex_x, rex_b = 1 - (v1 >> 7), 1 - ((v1 >> 6) & 1), 1 - ((v1 >> 5) & 1)
            vex_map = v1 & 0x1F
            key_head.extend((0xC4, v1 & 0x1F, v2 & 0x87))
            p += 2
        else:
            if p + 2 >= end:
                raise DecodeError('truncated evex')
            e1, e2, e3 = buf[p], buf[p + 1], buf[p + 2]
            rex_r, rex_x, rex_b = 1 - (e1 >> 7), 1 - ((e1 >> 6) & 1), 1 - ((e1 >> 5) & 1)
            vex_map = e1 & 0x03
            key_head.extend((0x62, e1 & 0x03, e2 & 0x87, e3 & 0xF7))
            p += 3
        if p >= end:
            raise DecodeError('truncated vex opcode')
        vop = buf[p]
        p += 1
        key_head.append(vop)
        ins.opcode = (0xC4, vex_map, vop)
        if vex_map == 1 and vop == 0x77:
            has_modrm = False
        elif vex_map in (1, 2, 3):
            has_modrm = True
            if vex_map == 3 or (vex_map == 1 and vop in (0x70, 0x71, 0x72, 0x73, 0xC2, 0xC4, 0xC5, 0xC6)):
                imm = 1
            group = vex_map == 1 and vop in (0x71, 0x72, 0x73)
        else:
            raise DecodeError('unsupported vex map')
    elif op == 0x0F:
        if p >= end:
            raise DecodeError('truncated 0f')
        op2 = buf[p]
        p += 1
        key_head.extend((0x0F, op2))
        if op2 == 0x38:
            if p >= end:
                raise DecodeError('truncated 0f38')
            key_head.append(buf[p])
            ins.opcode = (0x0F, 0x38, buf[p])
            p += 1
            has_modrm = True
        elif op2 == 0x3A:
            if p >= end:
                raise DecodeError('truncated 0f3a')
            key_head.append(buf[p])
            ins.opcode = (0x0F, 0x3A, buf[p])
            p += 1
            has_modrm = True
            imm = 1
        elif op2 == 0x0F:
            ins.opcode = (0x0F, 0x0F)
            has_modrm = True
            imm = 1
        else:
            ins.opcode = (0x0F, op2)
            if 0x80 <= op2 <= 0x8F:
                rel = 4
                ins.flow = JCC
            elif op2 in NO_MODRM_0F:
                if 0xC8 <= op2 <= 0xCF:
                    key_head[-1] = 0xC8
            else:
                has_modrm = True
                if op2 in IMM8_0F:
                    imm = 1
                group = op2 in GROUP_0F
                if op2 == 0x1F or op2 == 0x0D or (0x18 <= op2 <= 0x1E):
                    ins.flow = NOP
    else:
        if op in INVALID_1:
            raise DecodeError('opcode invalid in 64-bit mode: 0x%02x' % op)
        ins.opcode = (op,)
        key_head.append(op & 0xF8 if op in REG_IN_OPCODE1 else op)
        if op in MODRM1:
            has_modrm = True
            group = op in GROUP1
            if op in IMM8_1:
                imm = 1
            elif op in IMMZ_1:
                imm = 2 if opsize else 4
        elif op in IMM8_1:
            imm = 1
        elif op in IMMZ_1:
            imm = 2 if opsize else 4
        elif op in REL8_1:
            rel = 1
            ins.flow = JMP if op == 0xEB else JCC
        elif op in (0xE8, 0xE9):
            rel = 4
            ins.flow = CALL if op == 0xE8 else JMP
        elif 0xB8 <= op <= 0xBF:
            imm = 8 if rex_w else 2 if opsize else 4
        elif 0xA0 <= op <= 0xA3:
            imm = 4 if addrsize else 8
        elif op in (0xC2, 0xCA):
            imm = 2
            ins.flow = RET if op == 0xC2 else OTHER
        elif op == 0xC8:
            imm = 3
        elif op in (0xC3, 0xCB):
            ins.flow = RET
        elif op == 0xCC:
            ins.flow = INT3
        elif op == 0x90 and not rex_b:
            ins.flow = NOP
    if has_modrm:
        if p >= end:
            raise DecodeError('truncated modrm')
        reg_field = (buf[p] >> 3) & 7
        ins.reg = reg_field | (rex_r << 3)
        if ins.opcode == (0x8D,):
            ins.lea = True
        if len(ins.opcode) == 1:
            if op in (0xF6, 0xF7) and reg_field in (0, 1):
                imm = 1 if op == 0xF6 else (2 if opsize else 4)
            if op == 0xFF:
                if reg_field in (2, 3):
                    ins.flow = ICALL
                elif reg_field in (4, 5):
                    ins.flow = IJMP
        p, mod, rm, base, index, scale, disp, rip, mkey = _modrm(buf, p, end, rex_b, rex_x)
        if group:
            mkey[0] |= reg_field << 3
        key_head.extend(mkey)
        ins.base, ins.index = base, index
        if rip:
            ins.rip = disp[0] - start
            disp = None
        elif disp is not None:
            ins.disp = (disp[0] - start, disp[1], disp[2])
            # Stack-relative displacements depend on the host frame, not on the inlined body.
            if base != 4:
                key_head.extend(disp[2].to_bytes(4, 'little', signed=True))
    if rel:
        if p + rel > end:
            raise DecodeError('truncated branch')
        ins.rel = (p - start, rel)
        value = int.from_bytes(buf[p:p + rel], 'little', signed=True)
        p += rel
        ins.target = ip + (p - start) + value
    if imm:
        if p + imm > end:
            raise DecodeError('truncated immediate')
        key_head.extend(buf[p:p + imm])
        ins.imm = (p - start, imm)
        p += imm
    ins.length = p - start
    if ins.length > 15:
        raise DecodeError('instruction longer than 15 bytes')
    if ins.rip is not None:
        value = int.from_bytes(buf[start + ins.rip:start + ins.rip + 4], 'little', signed=True)
        ins.rip_target = ip + ins.length + value
    ins.key = bytes(key_head)
    return ins


def decode_range(buf, start, end, ip):
    """[(offset, Insn)] for buf[start:end] by linear sweep; `ip` is the address of buf[start]."""
    out = []
    p = start
    while p < end:
        ins = decode(buf, p, ip + (p - start), end)
        out.append((p - start, ins))
        p += ins.length
    return out
