"""Pinned source template for an owner-unknown static initializer family.

The input identifies one 16-byte entry-address interval. References are stand-ins;
the exact target bindings are supplied separately for each compiled unit.
"""
import hashlib
import json
from pathlib import Path

VERSION = '1'
FAMILY = 'static-descriptor-initializer'
BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def template_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def emit(rva, size):
    if type(rva) is not int or rva < 0 or type(size) is not int or size != 39:
        raise ValueError('unsupported initializer identity')
    base = rva & ~15
    cls = f'Static{base:x}'
    parameters = {'entry-rva': rva, 'size': size}
    origin = {'family': FAMILY, 'version': VERSION, 'template_digest': template_digest()}
    header = f'''// Build: {BUILD}
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// {cls}, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct {cls};
extern void construct({cls}*, const Descriptor*);
extern void destroy({cls}*);
struct {cls} {{
    void* value;
    {cls}() {{ construct(this, &descriptor); }}
    ~{cls}() {{ destroy(this); }}
}};
'''
    cpp = f'''// Build: {BUILD}; RVA 0x{rva:x}; {size} bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by GPT-6.1 Sol (recipe) and GPT-6.1 Terra (generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// object: GUESS(low) STANDIN
// Origin: {json.dumps(origin, sort_keys=True)}
#include "{cls}.h"
static {cls} object;
'''
    return cls, header, cpp, origin, parameters
