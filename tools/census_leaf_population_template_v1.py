"""Isolated ABI stand-ins for externally bound census leaf entries.

The synthetic classes are source containers, not recovered ownership claims.
Each unit has one compared method and one independently extracted reference.
"""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin(kind):
    if kind not in ('forward', 'address'):
        raise ValueError('unsupported population kind')
    return dict(family=f'census-{kind}-leaf', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(kind, rva, size):
    if type(rva) is not int or rva < 0 or type(size) is not int or size != {'forward': 5, 'address': 8}.get(kind):
        raise ValueError('unsupported leaf range')
    owner = f'Leaf{kind.title()}{rva:x}'
    method = 'Forward' if kind == 'forward' else 'Address'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; {size} bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis; no external implementation reused.
// Drafted by GPT-6.1 Sol, census leaf population template.
// Labels: v2
// {owner}, {method}, leaf_target, leaf_global: GUESS(low) STANDIN
// Owning system and original signature are unknown; the class is an ABI stand-in.
// Only {method} is compared. No original class, behavior or pointee type is claimed.
// Origin: {json.dumps(origin(kind), sort_keys=True)}
'''
    header = prefix + f'''#pragma once
class {owner} {{
public:
    void* {method}();
}};
'''
    declaration, body, external = (
        ('extern "C" void* leaf_target(void*);', 'return leaf_target(this);', 'leaf_target')
        if kind == 'forward' else
        ('extern unsigned char leaf_global;', 'return &leaf_global;', '?leaf_global@@3EA'))
    source = prefix + f'''#include "{owner}.h"
{declaration}
void* {owner}::{method}() {{ {body} }}
'''
    symbol = f'?{method}@{owner}@@QEAAPEAXXZ'
    return owner, method, header, source, symbol, external
