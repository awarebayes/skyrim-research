"""Original checked-copy wrapper; compiler SDK headers supply the library call.

No library implementation is copied or distributed. The ABI and original
ownership of each target are unassigned; an address-qualified helper is a guess.
"""
import hashlib
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='census-checked-copy', version='2',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva, size):
    if type(rva) is not int or rva <= 0 or type(size) is not int or size != 171:
        raise ValueError('unsupported checked-copy identity')
    owner = f'CheckedCopy{rva:x}'
    symbol = f'?Copy@{owner}@@SAHPEAX_KPEBX1@Z'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; {size} bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis; pinned compiler headers used normally, not copied.
// Original reconstruction: wrapper; no external implementation adapted into this file.
// Drafted by GPT-6.1 Sol, checked-copy template.
// Labels: v2
// {owner}, Copy, destination, destinationSize, source, count: GUESS(low) STANDIN
// Original name and ownership unknown; class is an ABI stand-in with no storage.
// Only compiled code is compared; no original class identity is claimed.
'''
    arguments = 'void* destination, unsigned __int64 destinationSize, const void* source, unsigned __int64 count'
    header = prefix + '#pragma once\n' + f'class {owner} {{\npublic:\n    static int Copy({arguments});\n}};\n'
    cpp = prefix + f'#include "{owner}.h"\n#include <string.h>\nint {owner}::Copy({arguments})' + ''' {
    return memcpy_s(destination, destinationSize, source, count);
}
'''
    return owner, symbol, header, cpp
