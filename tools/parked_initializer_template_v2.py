"""Natural resource/context initializer and resource teardown stamping templates.

Each cluster is a separate family. Target references are extracted per member;
stand-in types express only the dependencies of the selected generated function.
"""
import hashlib
import json
from pathlib import Path

VERSION = '2'
BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/o2-os.json'
EVIDENCE = 'findings/ghidra-import.md'


def template_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def emit(rva, size, cluster):
    expected = {0x8640: 116}
    if type(rva) is not int or rva < 0 or type(size) is not int or size != expected.get(cluster):
        raise ValueError('unsupported static identity')
    cls = f'Static{rva & ~15:x}'
    initializer = cluster == 0x8640
    family = 'parked-context-resource-initializer'
    origin = {'family': family, 'version': VERSION, 'template_digest': template_digest()}
    scope = ('Only the generated initializer and its EH cleanup funclets are compared; the registered teardown is a reference binding.'
             if initializer else 'Only the generated teardown and its EH scope are compared; constructor and manager implementations are reference bindings.')
    common = f'''// Build: {BUILD}
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis; possible sibling implementation exposure disclosed below.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/staging/blk_00cc0000_o2.cpp:13192 (ContextScope helper).
// ContextScope lineage is uncertain; conservatively treated as adapted from that sibling source.
// ContextScope: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); no licence is granted by its authors.
// Its README attributes some names to an Xbox 360 development-build PDB and Havok/Gamebryo source.
// Reuse is under the maintainer decision in LEGAL.md, not an infrastructure licence grant.
// Sibling material is not evidence about this target's names, addresses or behaviour.
// Drafted by GPT-6.1 Sol (recipe and generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// {scope}
// Labels: v2
'''
    header = common + f'''// {cls}, Manager, manager, reserved, construct, release, value: GUESS(low) STANDIN
#pragma once
struct {cls};
struct Manager {{
    virtual void reserved();
    virtual void construct({cls}*);
    virtual void release({cls}*);
}};
extern Manager* manager();
'''
    if initializer:
        header += f'''// current_context, previous, Storage: GUESS(low) STANDIN
// ContextScope: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)
// Thread-local storage models a separate context selection for each thread.
extern __declspec(thread) int current_context;
struct ContextScope {{
    int previous;
    ContextScope() : previous(current_context) {{ current_context = 102; }}
    ~ContextScope() {{ current_context = previous; }}
}};
struct Storage {{ void* value; ~Storage(); }};
struct {cls} {{
    Storage value;
    // Inline the thin scoped dispatch wrapper to avoid a separate constructor call for each static instance.
    __forceinline {cls}() {{ ContextScope scope; manager()->construct(this); }}
    ~{cls}();
}};
'''
    cpp = common + f'''// RVA 0x{rva:x}; {size} bytes
// object: GUESS(low) STANDIN
// Origin: {json.dumps(origin, sort_keys=True)}
#include "{cls}.h"
static {cls} object;
'''
    return cls, header, cpp, origin, {'entry-rva': rva, 'size': size}
