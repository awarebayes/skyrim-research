"""Natural C++ lifetime template for an inferred storage helper family.

Offsets and element size are input parameters; no enclosing object size is
claimed or forced. Byte-addressed field views avoid inventing padding or a
complete layout from the two observed accesses.
"""
import hashlib
import json
from pathlib import Path

VERSION = '2'
BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def template_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def emit(rva, size, parameters):
    values = [rva, size, *(parameters[k] for k in ('count-offset', 'storage-offset', 'element-size'))]
    if any(type(v) is not int or v < 0 for v in values) or not size or not parameters['element-size']:
        raise ValueError('invalid storage member parameters')
    if any(parameters[k] % 4 for k in ('count-offset', 'storage-offset')):
        raise ValueError('unaligned unsigned field')
    cls = f'StorageInit{rva:x}'
    origin = dict(family='storage-adapter-initializer', version=VERSION, template_digest=template_digest())
    common = f'''// Build: {BUILD}
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis; no external implementation source reused.
// Code origin: original reconstruction from binary analysis.
// Drafted by GPT-6.1 Sol (template and generator).
// Only initialize and its EH cleanup are compared; referenced implementations are bindings.
// Object identity, signature and adapter purpose are inferred, not recovered original names.
// Labels: v2
'''
    header = common + f'''// {cls}, AdapterBase, Adapter, owner, acquire, grow, release, initialize: GUESS(low) STANDIN
// storage_helper, count, storage, object: GUESS(low) STANDIN
#pragma once
struct AdapterBase {{
    virtual bool acquire(unsigned, unsigned) = 0;
    virtual bool grow(unsigned, unsigned, unsigned, unsigned, unsigned) = 0;
    virtual void release() = 0;
    virtual ~AdapterBase() {{}}
}};
struct {cls};
struct Adapter : AdapterBase {{
    void* owner;
    Adapter(void* object) : owner(object) {{}}
    bool acquire(unsigned, unsigned) override;
    bool grow(unsigned, unsigned, unsigned, unsigned, unsigned) override;
    void release() override;
    ~Adapter() override {{}}
}};
extern unsigned storage_helper(unsigned*, AdapterBase*, unsigned, unsigned);
// No size or complete layout is asserted for caller-owned storage.
struct {cls} {{ static unsigned initialize(void* object); }};
'''
    cpp = common + f'''// RVA 0x{rva:x}; {size} bytes
// Origin: {json.dumps(origin, sort_keys=True)}
#include "{cls}.h"
unsigned {cls}::initialize(void* object)
{{
    Adapter adapter(object);
    unsigned& count = *reinterpret_cast<unsigned*>(static_cast<char*>(object) + {parameters['count-offset']});
    unsigned& storage = *reinterpret_cast<unsigned*>(static_cast<char*>(object) + {parameters['storage-offset']});
    return storage_helper(&storage, &adapter, count, {parameters['element-size']});
}}
'''
    return cls, header, cpp, origin
