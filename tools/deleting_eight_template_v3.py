"""Plain eight-byte virtual-interface stamp: no synthesized object storage."""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='scalar-deleting-eight-byte-leaf', version='3',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva, object_size):
    if type(rva) is not int or rva < 0 or type(object_size) is not int or object_size != 8:
        raise ValueError('eight-byte interface only; no storage-bearing class admitted')
    cls = f'DeletingLeaf{rva:x}'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; 43 bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by tools/deleting_eight_template_v3.py (GPT-6.1 Sol).
// Labels: v2
// {cls}, object: GUESS(low) STANDIN
// Original owner and interface identity are unknown.
// Object state is only the compiler's virtual table pointer; no data members are added.
// Only the compiler-emitted scalar deleting destructor is compared.
// Static object forces emission; its initializer and teardown are not compared.
// No external implementation is copied; a pass proves code, not original names.
// Origin: {json.dumps(origin(), sort_keys=True)}
'''
    header = prefix + f'''#pragma once
void operator delete(void*, unsigned __int64) noexcept;
class {cls} {{
public:
    virtual ~{cls}() {{}}
}};
static_assert(sizeof({cls}) == 8, "minimal virtual interface size");
'''
    source = prefix + f'#include "{cls}.h"\nstatic {cls} object;\n'
    return dict(cls=cls, header=header, source=source,
                symbol=f'??_G{cls}@@UEAAPEAXI@Z', table=f'??_7{cls}@@6B@',
                deallocator='??3@YAXPEAX_K@Z')
