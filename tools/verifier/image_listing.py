"""Candidate listing for one function taken from a linked image (DLL) by its map file.

A `/GL` object holds no machine code, so a whole-program build can only be compared after the
link. This turns one function of the linked candidate image into the same kind of listing
`align.py` reads from an object (`llvm-objdump -d -r`): every rip-relative operand and every
direct call or jump that leaves the function is rewritten as a relocation against the map symbol
it lands in, with the offset into that symbol as the addend, so `align.py` resolves it through the
task symbol map exactly as it does for an object.

    tools/verifier/image_listing.py --image cand.dll --map cand.map --symbol SYM [--alias aliases.json] \
        [--objdump llvm-objdump] --out listing.txt

`--alias` maps stand-in symbol names (stubs bound with /ALTERNATENAME for externals the unit does
not define) back to the external they replace. The function's extent runs to the next map
symbol, less trailing int3 padding. The listing is game-derived when the source is (G2): write
it under .local/ only. Standard output carries only counts. A reading aid, not comparator input:
the comparator does not yet take functions from a linked image.
"""
import argparse
import bisect
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import INSN  # noqa: E402  same row format as the object listings align.py reads

MAP_ROW = re.compile(r'^\s*[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16})\s', re.I)
RIP = re.compile(r'\[rip ([+-]) (0x[0-9a-f]+)\]')
BRANCH = re.compile(r'^(call|jmp|j[a-z]+)\s+(0x[0-9a-f]+)')


def read_map(path):
    """Sorted [(address, name)] of every public and static symbol row in an MSVC map file."""
    rows = {}
    for line in Path(path).read_text(errors='replace').splitlines():
        m = MAP_ROW.match(line)
        if m:
            rows.setdefault(int(m.group(2), 16), m.group(1))
    return sorted(rows.items())


def locate(symtab, addrs, va):
    """(name, offset) of the map symbol containing va, or (None, 0)."""
    i = bisect.bisect_right(addrs, va) - 1
    if i < 0:
        return None, 0
    return symtab[i][1], va - symtab[i][0]


def listing(image, mapfile, symbol, objdump, aliases=None):
    """(listing text, stats) for one function of the image."""
    aliases = aliases or {}
    symtab = read_map(mapfile)
    addrs = [a for a, _ in symtab]
    starts = [a for a, n in symtab if n == symbol]
    if not starts:
        raise ValueError('symbol not in map')
    start = starts[0]
    nxt = addrs[bisect.bisect_right(addrs, start)] if bisect.bisect_right(addrs, start) < len(addrs) else start + 0x1000
    out = subprocess.run([objdump, '-d', '--x86-asm-syntax=intel', f'--start-address={start:#x}',
                          f'--stop-address={nxt:#x}', str(image)], capture_output=True, text=True, timeout=120)
    rows = []
    for line in out.stdout.splitlines():
        m = INSN.match(line)
        if m:
            rows.append([int(m.group(1), 16), m.group(2).split(), ' '.join(m.group(3).split())])
    while rows and rows[-1][2] == 'int3':
        rows.pop()
    end = rows[-1][0] + len(rows[-1][1]) if rows else start
    lines, stats = [], {'instructions': len(rows), 'size': end - start, 'relocs': 0, 'unnamed': 0}
    for addr, data, text in rows:
        next_ip = addr + len(data)
        relocs = []
        body = re.sub(r'\s*<[^>]*>', '', text)
        m = RIP.search(body)
        if m:
            disp = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            name, off = locate(symtab, addrs, next_ip + disp)
            field = bytes.fromhex(''.join(data)).find((disp & 0xffffffff).to_bytes(4, 'little'), 1)
            if name is not None and field > 0:
                body = body[:m.start()] + f'[rip + {off:#x}]' + body[m.end():]
                relocs.append((addr + field, 'IMAGE_REL_AMD64_REL32', aliases.get(name, name)))
            else:
                stats['unnamed'] += 1
        b = BRANCH.match(body)
        if b:
            dest = int(b.group(2), 16)
            if not start <= dest < end and len(data) >= 5:
                name, off = locate(symtab, addrs, dest)
                if name is not None:
                    body = f'{b.group(1)} {next_ip + off:#x}' + body[b.end():]
                    relocs.append((next_ip - 4, 'IMAGE_REL_AMD64_REL32', aliases.get(name, name)))
                else:
                    stats['unnamed'] += 1
        lines.append(f'{addr:x}: {" ".join(data)} \t{body}')
        for field, kind, name in relocs:
            lines.append(f'\t\t{field:016x}:  {kind}\t{name}')
            stats['relocs'] += 1
    return '\n'.join(lines) + '\n', stats


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--image', required=True)
    p.add_argument('--map', required=True)
    p.add_argument('--symbol', required=True)
    p.add_argument('--alias', help='JSON object: stand-in symbol -> replaced external')
    p.add_argument('--objdump', default='llvm-objdump')
    p.add_argument('--out', required=True)
    a = p.parse_args(argv)
    aliases = json.loads(Path(a.alias).read_text()) if a.alias else {}
    try:
        text, stats = listing(a.image, a.map, a.symbol, a.objdump, aliases)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    Path(a.out).write_text(text)
    print(' '.join(f'{k}={v}' for k, v in stats.items()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
