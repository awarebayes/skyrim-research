"""Generic private-contract extraction for decoded instructions and MSVC EH metadata.

No target instruction predicates live here. A caller supplies its private full-row
regular expressions and numeric capture rules. Instruction text comes from the
existing LLVM disassembler. EH structures reuse the comparator's PE reader;
layout and version checks are delegated to the existing pecoff reader.
All extracted rows and contracts belong under .local, never in public tooling.
"""
import re
import struct

from pecoff import unwind_header


def extract_instructions(rows, image_base, contract):
    """Match every instruction, returning the explicitly configured captures.

    Each contract item has pattern and captures; capture rules have group, base
    (10 or 16), and relative (whether an absolute address becomes an RVA).
    No code bytes are read, returned or stored by this function.
    """
    if len(rows) != len(contract):
        raise ValueError('instruction count differs from private contract')
    result = {}
    for row, rule in zip(rows, contract):
        match = re.fullmatch(rule['pattern'], row[2])
        if not match:
            raise ValueError('instruction differs from private contract')
        for name, capture in rule.get('captures', {}).items():
            if name in result or capture.get('base', 16) not in (10, 16):
                raise ValueError('duplicate capture or unsupported numeric base')
            value = int(match[capture['group']], capture.get('base', 16))
            if capture.get('relative', False):
                value -= image_base
                if value < 0:
                    raise ValueError('reference precedes image base')
            result[name] = value
    return result


def extract_eh(image, rva, procedures, handler_rva):
    """Read FuncInfo and all unwind actions, bound to an expected C++ handler.

    Returns integer metadata only. to-state values remain signed, so transitions
    to the initial state are not conflated with large unsigned state numbers.
    """
    entries = procedures.get(rva, [])
    if len(entries) != 1:
        raise ValueError('ambiguous primary unwind')
    unwind = entries[0]
    head = image.read(unwind, 4, 'unwind header')[1]
    flags, offset = unwind_header(head, 'storage extraction')
    if not flags & 3 or flags & 4:
        raise ValueError('missing or chained EH handler')
    handler, info = struct.unpack('<II', image.read(unwind + offset, 8, 'handler data')[1])
    if handler != handler_rva:
        raise ValueError('unexpected EH handler')
    fields = struct.unpack('<10I', image.read(info, 40, 'FuncInfo')[1])
    # The existing parser refuses unsupported FuncInfo versions and bad tables.
    image.funcinfo_entries(info)
    if fields[1] > 65536:
        raise ValueError('unreasonable unwind state count')
    actions = [struct.unpack('<iI', image.read(fields[2] + 8*i, 8, 'unwind action')[1])
               for i in range(fields[1])]
    if any(state < -1 or state >= fields[1] for state, _ in actions):
        raise ValueError('unwind state outside FuncInfo')
    return {'handler-rva': handler, 'funcinfo-rva': info, 'unwind-states': fields[1],
            'try-blocks': fields[3], 'eh-flags': fields[9], 'actions': actions}
