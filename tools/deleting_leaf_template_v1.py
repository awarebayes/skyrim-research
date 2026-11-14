"""Natural compiler-emitted scalar deleting destructor, minimal ABI stand-in."""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='scalar-deleting-leaf', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva, object_size):
    if type(rva) is not int or rva < 0 or type(object_size) is not int or not 8 <= object_size <= 1048576 or object_size % 8:
        raise ValueError('unsupported identity or allocation size')
    cls = f'DeletingLeaf{rva:x}'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; 43 bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by tools/deleting_leaf_template_v1.py (GPT-6.1 Sol).
// Labels: v2
// {cls}, storage, object: GUESS(low) STANDIN
// Original owner, inheritance, members and destructor signature are unknown.
// Sized deletion argument is observed; opaque storage only reproduces that size.
// Only the compiler-emitted scalar deleting destructor is compared.
// The global object forces emission; its initializer and teardown are not compared.
// No external implementation is copied; a pass proves code, not names or layout.
// Origin: {json.dumps(origin(), sort_keys=True)}
'''
    storage = f'    unsigned char storage[{object_size - 8}];\n' if object_size > 8 else ''
    header = prefix + f'''#pragma once
void operator delete(void*, unsigned __int64) noexcept;
class {cls} {{
public:
    virtual ~{cls}() {{}}
{storage}}};
static_assert(sizeof({cls}) == {object_size}, "observed sized deletion argument");
'''
    source = prefix + f'#include "{cls}.h"\nstatic {cls} object;\n'
    return dict(cls=cls, header=header, source=source,
                symbol=f'??_G{cls}@@UEAAPEAXI@Z', table=f'??_7{cls}@@6B@',
                deallocator='??3@YAXPEAX_K@Z')
