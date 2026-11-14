"""Eight-byte interface layout and its compiler-emitted deleting destructor.

The destructor body remains external. No data fields are introduced to set a size.
"""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='scalar-deleting-eight-byte-wrapper', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva, object_size=8):
    if type(rva) is not int or rva < 0 or type(object_size) is not int or object_size != 8:
        raise ValueError('this version represents only an eight-byte interface')
    cls = f'DeletingWrapper{rva:x}'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; 52 bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by tools/deleting_wrapper_template_v1.py (GPT-6.1 Sol).
// Labels: v2
// {cls}, object: GUESS(low) STANDIN
// Interface has a virtual destructor and no represented data members.
// Original ownership and additional virtual methods are not recovered here.
// The complete destructor is external and independently bound for this member.
// Only the compiler-emitted scalar deleting destructor is compared.
// Global object requests normal virtual-table and wrapper emission.
// No external implementation is copied; a pass proves no name or original layout.
// Origin: {json.dumps(origin(), sort_keys=True)}
'''
    header = prefix + f'''#pragma once
void operator delete(void*, unsigned __int64) noexcept;
class {cls} {{
public:
    virtual ~{cls}();
}};
static_assert(sizeof({cls}) == 8, "interface layout");
'''
    source = prefix + f'#include "{cls}.h"\nstatic {cls} object;\n'
    return dict(cls=cls, header=header, source=source,
                symbol=f'??_G{cls}@@UEAAPEAXI@Z',
                destructor=f'??1{cls}@@UEAA@XZ', deallocator='??3@YAXPEAX_K@Z')
