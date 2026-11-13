"""Pinned pilot templates for empty, forwarding and global-address methods.

These are minimal ABI stand-ins. Passing code comparison does not establish the
original signature, ownership, names or suitability for family acceptance.
"""
import hashlib
import json
from pathlib import Path
import re

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'
KINDS = ('empty', 'forward', 'address')
IDENT = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')


def emit(owner, kind, virtual):
    if not IDENT.fullmatch(owner) or kind not in KINDS or type(virtual) is not bool:
        raise ValueError('unsupported pilot identity')
    method = {'empty': 'CensusEmpty', 'forward': 'CensusForward', 'address': 'CensusAddress'}[kind]
    result = 'void' if kind == 'empty' else 'void*'
    h = f'''#pragma once
class {owner} {{
public:
    {'virtual ' if virtual else ''}{result} {method}();
}};
'''
    declaration, expression = {
        'empty': ('', ''),
        'forward': ('extern "C" void* census_target(void*);\n', 'return census_target(this);'),
        'address': ('extern unsigned char census_global;\n', 'return &census_global;'),
    }[kind]
    cpp = f'''#include "{owner}.h"
{declaration}{result} {owner}::{method}() {{ {expression} }}
'''
    return method, h, cpp


def origin(kind):
    if kind not in KINDS:
        raise ValueError('unsupported pilot kind')
    return dict(family=f'census-{kind}-method', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def header(owner, method, kind, *, rva, size, owner_is_rtti):
    return f'''// Build: {BUILD}; RVA 0x{rva:x}; {size} bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by GPT-6.1 Sol, bounded census pilot template.
// Labels: v2
// {owner}: {'EXE_RTTI' if owner_is_rtti else 'GUESS(low)'}
// {method}, census_target, census_global: GUESS(low) STANDIN
// Only {method} is compared. The original signature is unknown.
// Declaration and return type are minimal stand-ins for the observed ABI shape.
// No original body or external implementation is copied; no runtime behavior claim.
// Origin: {json.dumps(origin(kind), sort_keys=True)}
'''
