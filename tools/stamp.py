"""Conservative primitives for script-produced reconstruction candidates.

This module does not submit candidates or confer match status.  Callers must supply
independently established identities and reference bindings and run the verifier.
"""
import re


IDENT = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
GENERATOR_VERSION = '1'


class UnsafeCandidate(ValueError):
    """The candidate cannot be emitted safely by this generator."""


def validate_identity(owner, method, *, existing_classes, names, name_rva, rva):
    """Reject identities whose class or function conflicts with existing inputs.

    ``names`` maps a qualified public name to all RVAs carrying that name.  The
    caller must populate it from the whole inventory, not just selected candidates.
    """
    if '<' in owner or '>' in owner or '__' in owner:
        raise UnsafeCandidate('template-owned')
    parts = owner.split('::')
    if not all(IDENT.fullmatch(part) for part in parts) or not IDENT.fullmatch(method):
        raise UnsafeCandidate('unsupported-name')
    if owner in existing_classes or parts[-1] in existing_classes:
        raise UnsafeCandidate('existing-unit')
    qualified = f'{owner}::{method}'
    if name_rva != rva or set(names.get(qualified, ())) != {rva}:
        raise UnsafeCandidate('name-clash')
    return qualified


def validate_bindings(reference_fields, bindings):
    """Require one exact target binding per reference field, with no extras.

    Values are RVAs from the member's own independently decoded reference map.
    The comparator remains responsible for verifying the compiled reference.
    """
    if set(reference_fields) != set(bindings):
        raise UnsafeCandidate('reference-fields')
    if any(bindings[field] != target for field, target in reference_fields.items()):
        raise UnsafeCandidate('wrong-target')


def emit_leaf(owner, method, *, family, width, value, virtual, name_label):
    """Return a self-contained header/source pair for a narrow leaf candidate.

    ``value`` is the immediate for a constant, or the member byte offset for a
    member and member-address.  This emitter deliberately does not decode an
    executable or decide whether an identity is safe.
    """
    if family not in ('constant', 'member', 'member-address'):
        raise UnsafeCandidate('unsupported-family')
    if width not in (1, 4, 8) or (family == 'constant' and width == 8):
        raise UnsafeCandidate('unsupported-width')
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise UnsafeCandidate('invalid-parameter')
    if family == 'constant' and value >= 1 << (width * 8):
        raise UnsafeCandidate('invalid-parameter')
    parts = owner.split('::')
    if not all(IDENT.fullmatch(p) for p in parts) or not IDENT.fullmatch(method):
        raise UnsafeCandidate('unsupported-name')
    if name_label != 'GUESS(low)' and not re.fullmatch(r'COMMUNITY\([^()\r\n]+\)', name_label):
        raise UnsafeCandidate('name-origin')
    if family != 'constant' and value < (8 if virtual else 0):
        raise UnsafeCandidate('invalid-offset')
    types = {1: 'std::uint8_t', 4: 'std::uint32_t', 8: 'void*'}
    member_type = types[width]
    result_type = member_type + ' const*' if family == 'member-address' else member_type
    pad = value - (8 if virtual else 0)
    if family != 'constant' and (value % width or pad > 0x100000):
        raise UnsafeCandidate('invalid-offset')
    label = f'// GENERATED({family}@{GENERATOR_VERSION}); {name_label}'
    if name_label == 'GUESS(low)':
        label += '; method name inferred from vtable owner and slot'
    h = ['#pragma once', '#include <cstdint>', label]
    for ns in parts[:-1]:
        h.append(f'namespace {ns} {{')
    h.extend([f'class {parts[-1]}', '{', 'public:',
              f'    {"virtual " if virtual else ""}{result_type} {method}() const;'])
    if family != 'constant':
        if pad:
            h.append(f'    std::uint8_t padding[0x{pad:x}];')
        h.append(f'    {member_type} member;')
    h.append('};')
    h.extend('}' for _ in parts[:-1])
    expression = (f'0x{value:x}' if family == 'constant' else
                  ('&member' if family == 'member-address' else 'member'))
    cpp = ['#include "unit.h"', label, f'{result_type} {owner}::{method}() const', '{',
           f'    return {expression};', '}']
    return '\n'.join(h) + '\n', '\n'.join(cpp) + '\n'
