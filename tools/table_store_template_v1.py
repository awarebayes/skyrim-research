"""Natural polymorphic destructor for an RTTI-bound primary-table store leaf."""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='primary-table-store-leaf', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva):
    if type(rva) is not int or rva < 0:
        raise ValueError('invalid member RVA')
    cls = f'TableStoreLeaf{rva:x}'
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; 11 bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by tools/table_store_template_v1.py (GPT-6.1 Sol).
// Labels: v2
// {cls}, {cls}::~{cls}: GUESS(low) STANDIN
// The stored table is bound through its primary RTTI complete object locator.
// Represented layout: the compiler-managed primary virtual pointer only.
// Other members, bases, total object size and original destructor role are unknown.
// No opaque storage or size-forcing declaration; no full-layout claim is made.
// This empty virtual destructor is an ABI stand-in for the compared table store.
// No external implementation is copied; a pass proves code, not names or behaviour.
// Origin: {json.dumps(origin(), sort_keys=True)}
'''
    header = prefix + f'''#pragma once
class {cls} {{
public:
    virtual ~{cls}();
}};
'''
    source = prefix + f'#include "{cls}.h"\n{cls}::~{cls}() {{}}\n'
    return dict(cls=cls, header=header, source=source,
                symbol=f'??1{cls}@@UEAA@XZ', table=f'??_7{cls}@@6B@')
