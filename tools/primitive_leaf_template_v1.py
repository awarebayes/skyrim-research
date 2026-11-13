"""Pinned minimal source forms for trivial leaf entries and empty static teardown.

Leaf interval units are source stand-ins, not claims of original class ownership.
"""
import hashlib
import json
from pathlib import Path

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin(family):
    if family not in ('empty', 'constant'):
        raise ValueError('unsupported primitive family')
    return dict(family=f'primitive-{family}-entry', version='1',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def emit(rva, size, family, kind, value=None):
    if type(rva) is not int or rva < 0 or type(size) is not int:
        raise ValueError('invalid entry identity')
    if (family == 'empty' and (size != 3 or kind not in ('ordinary', 'teardown'))
            or family == 'constant' and (size != 6 or kind != 'ordinary'
                                        or type(value) is not int or not 0 <= value < 2**32)
            or family not in ('empty', 'constant')):
        raise ValueError('unsupported primitive parameters')
    static = kind == 'teardown'
    cls = f'Static{rva & ~15:x}' if static else f'Leaf{rva:x}'
    area = 'static' if static else 'leaves'
    method = 'teardown' if static else 'Invoke'
    parameters = dict(entry_rva=rva, size=size, kind=kind)
    if family == 'constant':
        parameters['value'] = value
    prefix = f'''// Build: {BUILD}; RVA 0x{rva:x}; {size} bytes
// Evidence: {EVIDENCE}
// Recipe: {RECIPE}
// Source exposure: binary-analysis
// Drafted by tools/primitive_leaf_template_v1.py (GPT-6.1 Sol).
// Labels: v2
// {cls}, Invoke, object, construct: GUESS(low) STANDIN
// Owning system and original function signature are unknown.
// This interval unit is a minimal source stand-in, not an original class identity.
// Only the {'generated teardown' if static else 'Invoke leaf'} is compared.
// Other declarations and generated functions exist only to express its source form.
// No external implementation is copied; a pass proves code, not names or behavior.
// Origin: {json.dumps(origin(family), sort_keys=True)}
'''
    if static:
        h = f'''#pragma once
struct {cls};
extern void construct({cls}*);
struct {cls} {{
    {cls}() {{ construct(this); }}
    ~{cls}() {{}}
}};
'''
        cpp = f'#include "{cls}.h"\nstatic {cls} object;\n'
        symbol = '??__Fobject@@YAXXZ'
    else:
        result = 'void' if family == 'empty' else 'unsigned int'
        qualifier = '' if family == 'empty' else ' const'
        body = '' if family == 'empty' else f'return {value}u;'
        h = f'#pragma once\nclass {cls} {{\npublic:\n    {result} Invoke(){qualifier};\n}};\n'
        cpp = f'#include "{cls}.h"\n{result} {cls}::Invoke(){qualifier} {{ {body} }}\n'
        symbol = f'?Invoke@{cls}@@' + ('QEAAXXZ' if family == 'empty' else 'QEBAIXZ')
    return dict(cls=cls, area=area, method=method, header=prefix+h, source=prefix+cpp,
                symbol=symbol, parameters=parameters, origin=origin(family))
