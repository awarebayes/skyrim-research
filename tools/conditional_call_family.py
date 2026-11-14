"""Original bounded callback-dispatch template and fail-closed per-member extraction.

No image data is embedded here. The caller supplies a pinned image and a freshly
compiled template object. Reference targets are decoded independently for every
member; the complete remaining instruction stream must equal the template.
"""
import hashlib
import struct
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parent / 'analysis')]
import imagemodel

VERSION = '1'
BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
CLASS = 'ConditionalVirtualCall'
STATE = 'conditional_call_state'
CALLBACK = 'conditional_call_callback'


def symbol(rva):
    if type(rva) is not int or rva <= 0:
        raise ValueError('invalid member identity')
    return f'ConditionalCallAt{rva:x}'


def emit(members):
    """One guessed interface, independent externally named free helpers, no storage."""
    if not members or len(set(members)) != len(members):
        raise ValueError('empty or duplicate population')
    header = (f'// Build: {BUILD}\n// Labels: v2\n'
              '// Source exposure: binary-analysis; original declarations and linkage unknown.\n'
              '// Adapted bodies: none; original bounded callback-dispatch template.\n'
              '// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.\n'
              f'// {CLASS}, invoke, object, {STATE}, {CALLBACK}: GUESS(low) STANDIN\n')
    h = header + '#pragma once\n' + f'struct {CLASS} {{ virtual void invoke(unsigned int); }};\n'
    h += f'extern void* {STATE};\nextern void (*{CALLBACK})({CLASS}*);\n'
    cpp = header + ''.join(f'// RVA 0x{r:x}; 53 bytes\n' for r in members) + f'// Recipe: {RECIPE}\n// Evidence: findings/ghidra-import.md\n'
    cpp += '// Drafted by tools/conditional_call_family.py (Codex GPT-6.1 Sol).\n'
    cpp += '// External C linkage identifies candidates only; original language and linkage are unassigned.\n'
    cpp += '#include "ConditionalVirtualCall.h"\n'
    for rva in members:
        name = symbol(rva)
        label = f'// {name}: GUESS(low); address-qualified helper name, not a recovered symbol\n'
        h += label + f'extern "C" void {name}({CLASS}* object);\n'
        cpp += f'// Build: {BUILD}; RVA 0x{rva:x}; 53 bytes\n' + label
        cpp += f'''extern "C" void {name}({CLASS}* object) {{
    if (object) {{
        object->invoke(0);
        if ({STATE} && {CALLBACK}) {CALLBACK}(object);
    }}
}}
'''
    return h, cpp


def extract(image, rva, size, candidate, candidate_symbol):
    """Validate full shape, local branches and every external reference field.

    This is an enrollment filter, never comparator evidence. The unchanged
    comparator independently checks code, relocation targets and unwind scope.
    """
    matches = [s for s in candidate.symbols.values() if s.name == candidate_symbol
               and s.is_function and s.storage == 2 and s.value == 0]
    if len(matches) != 1:
        raise ValueError('candidate identity is not unique external function')
    section = candidate.section(matches[0].section)
    if len(section.data) != size:
        raise ValueError('candidate extent differs')
    code = image.read(rva, size, 'conditional-call member')[1]
    fields, instructions, flags, end = imagemodel.field_records(
        code, rva, size, image.image_base, rva + size)
    if flags or end != size:
        raise ValueError('unsupported complete decoded shape')
    expected = {}
    for rel in section.relocs:
        if rel.kind not in range(4, 10) or rel.offset in expected:
            raise ValueError('unsupported candidate reference')
        expected[rel.offset] = (4, 'REL32', rel.kind - 4,
                                candidate.symbols[rel.symbol].name)
    actual = {off: (width, kind, tail, target) for off, width, kind, tail, target in fields}
    if len(actual) != len(fields) or set(actual) != set(expected) or len(actual) != 2:
        raise ValueError('reference field shape differs')
    masked_target, masked_candidate = bytearray(code), bytearray(section.data)
    bindings = {}
    for off, (width, kind, tail, name) in expected.items():
        aw, ak, at, target = actual[off]
        if (aw, ak, at) != (width, kind, tail) or not isinstance(target, int):
            raise ValueError('reference kind differs')
        independent = rva + off + width + tail + struct.unpack_from('<i', code, off)[0]
        if target != independent or image.section_for(target) is None or name in bindings:
            raise ValueError('invalid per-member target binding')
        bindings[name] = target
        masked_target[off:off + width] = bytes(width)
        masked_candidate[off:off + width] = bytes(width)
    if masked_target != masked_candidate:
        raise ValueError('complete instruction shape differs')
    if not any(STATE in n for n in bindings) or not any(CALLBACK in n for n in bindings):
        raise ValueError('unexpected template reference names')
    return bindings


def digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
