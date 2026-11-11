"""Private side-by-side disassembly of a target function and a candidate, for a Drafter's next try.

Runs locally with llvm-objdump on the candidate object and the pinned image. The output is
game-derived (G2): it is written only under a `.local/` task directory and never printed, never
sent through `boat exec` and never committed. It is a reading aid, not evidence; the comparator
alone decides a match.
"""
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

INSN = re.compile(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$')
RELOC = re.compile(r'^\s*([0-9a-f]+):\s+(IMAGE_REL_\S+)\s+(.*)$')
CANDIDATES = ('llvm-objdump', '/opt/homebrew/opt/llvm/bin/llvm-objdump', '/usr/local/opt/llvm/bin/llvm-objdump')


def find_objdump(configured=None):
    for name in ([configured] if configured else []) + [os.environ.get('SR_OBJDUMP')] + list(CANDIDATES):
        if name and (shutil.which(name) or (os.path.isfile(name) and os.access(name, os.X_OK))):
            return shutil.which(name) or name
    return None


def image_base(path):
    with open(path, 'rb') as f:
        head = f.read(4096)
    (pe,) = struct.unpack_from('<I', head, 0x3c)
    if head[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', head, pe + 24)[0] != 0x20b:
        raise ValueError('not a PE32+ image')
    return struct.unpack_from('<Q', head, pe + 24 + 24)[0]


def parse(text, start):
    """[(offset, bytes, text, relocation offsets)] from llvm-objdump output; relocations are appended to the text."""
    rows = []
    for line in text.splitlines():
        m = INSN.match(line)
        if m:
            rows.append([int(m.group(1), 16) - start, m.group(2).strip(), ' '.join(m.group(3).split()), []])
            continue
        r = RELOC.match(line)
        if r and rows:
            rows[-1][2] += f'  <{r.group(2).replace("IMAGE_REL_AMD64_", "")} {r.group(3).strip()}>'
            rows[-1][3].append(int(r.group(1), 16) - start)
    return rows


def masked(row, relocs):
    """The row's bytes with each 4-byte relocated field blanked, so placeholder bytes compare equal."""
    data = row[1].split()
    for off in relocs:
        for i in range(off - row[0], off - row[0] + 4):
            if 0 <= i < len(data):
                data[i] = '..'
    return data


def target_rows(objdump, image, rva, size):
    base = image_base(image)
    out = subprocess.run([objdump, '-d', '--x86-asm-syntax=intel', f'--start-address=0x{base + rva:x}',
                          f'--stop-address=0x{base + rva + size:x}', str(image)],
                         capture_output=True, text=True, timeout=120)
    return parse(out.stdout, base + rva)


def candidate_rows(objdump, obj, symbol):
    out = subprocess.run([objdump, '-d', '-r', '--x86-asm-syntax=intel', f'--disassemble-symbols={symbol}', str(obj)],
                         capture_output=True, text=True, timeout=120)
    return parse(out.stdout, 0)


def side_by_side(target, candidate, width=58):
    """Aligned by instruction index; `*` marks rows whose bytes differ outside relocated fields.

    A candidate's relocated field holds a placeholder until link time, so a row that differs only
    there is not marked; whether the reference resolves to the right target is the comparator's call.
    """
    lines = [f'  {"off":>5}  {"target":<{width}}  {"off":>5}  candidate',
             f'  {"":>5}  {"-" * width}  {"":>5}  {"-" * width}']
    first = None
    for i in range(max(len(target), len(candidate))):
        t = target[i] if i < len(target) else None
        c = candidate[i] if i < len(candidate) else None
        differs = t is None or c is None or (t[1] != c[1] and (
            t[0] != c[0] or masked(t, c[3]) != masked(c, c[3])))
        if differs and first is None:
            first = i
        left = f'{t[0]:>5x}  {t[2][:width]:<{width}}' if t else f'{"":>5}  {"":<{width}}'
        right = f'{c[0]:>5x}  {c[2]}' if c else ''
        lines.append(f'{"*" if differs else " "} {left}  {right}')
    summary = (f'target {len(target)} instructions, candidate {len(candidate)}; '
               + ('identical instruction bytes' if first is None else f'first differing row {first}'))
    return '\n'.join([summary] + lines) + '\n'


def write_side_by_side(dest, objdump, image, obj, symbol, rva, size):
    """Write the comparison file and return its path, or None with a reason when it cannot be made."""
    if objdump is None:
        return None, 'llvm-objdump not found (set SR_OBJDUMP)'
    if image is None or not Path(image).is_file():
        return None, 'no local image configured (.local/verifier/config.json "image")'
    if not Path(obj).is_file():
        return None, 'no candidate object'
    try:
        text = side_by_side(target_rows(objdump, image, rva, size), candidate_rows(objdump, obj, symbol))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return None, f'disassembly failed: {exc}'
    Path(dest).write_text(text)
    return Path(dest), None
