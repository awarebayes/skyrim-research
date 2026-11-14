"""Represent fieldless registration products and emit ordinary overriding classes.

Input identities, inheritance and sizes come from private, per-member RTTI
reconciliation. No target instruction strings, encoded constants or bytes occur
here. The only compared code is an MSVC-emitted secondary destructor adjustor.
"""
import hashlib
import json
from pathlib import Path
import re

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/ghidra-import.md'


def origin():
    return dict(family='represented-adjustor-thunk', version='2',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z_]\w*', value):
        raise ValueError('plain C++ identifier required')
    return value


def prefix():
    return f'''// Build: {BUILD}
// Evidence: {EVIDENCE}
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v2.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
'''


def registration_base():
    return prefix()+'''// AutoRegisterCombatObject, CombatInventoryItemMagicT: EXE_RTTI
// AutoRegisterCombatObjectLayout: GUESS(medium) STANDIN
// CombatInventoryItemMagic, CombatInventoryItemShout, CombatInventoryItemStaff,
// CombatInventoryItemPotion, CombatInventoryItemScroll: EXE_RTTI
// Product, Inventory, Caster: GUESS(medium); template-parameter spellings
// Independent base deletion sizes agree with a fieldless polymorphic specialization.
#pragma once
namespace ResearchLayouts {
class CombatInventoryItemMagic;
class CombatInventoryItemShout;
class CombatInventoryItemStaff;
class CombatInventoryItemPotion;
class CombatInventoryItemScroll;
template<class Inventory, class Caster> class CombatInventoryItemMagicT;
template<class Product>
class AutoRegisterCombatObjectLayout {
public:
    virtual ~AutoRegisterCombatObjectLayout();
};
static_assert(sizeof(AutoRegisterCombatObjectLayout<void>) == sizeof(void*), "fieldless registration base");
}
'''


def registration_owner(caster, inventory, size):
    identifier(caster)
    if type(size) is not int or size <= 0 or not inventory or len(set(inventory)) != len(inventory):
        raise ValueError('distinct represented product types and positive size required')
    for value in inventory:
        identifier(value)
    cls = f'AutoRegister{caster}Layout'
    bases = [f'AutoRegisterCombatObjectLayout<{caster}>']
    bases += [f'AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<{value}, {caster}>>' for value in inventory]
    return cls, prefix()+f'''// AutoRegisterCombatMagicCaster, {caster}: EXE_RTTI
// {cls}: GUESS(medium) STANDIN; layout-only spelling for the RTTI specialization
// RTTI lists each product specialization as a distinct nonvirtual direct base.
// Each base size is independently reconciled; the owner allocation size is checked.
#pragma once
#include "AutoRegisterCombatObjectLayout.h"
namespace ResearchLayouts {{
class {caster};
class {cls} :
    public '''+',\n    public '.join(bases)+f''' {{
public:
    ~{cls}() override;
}};
static_assert(sizeof({cls}) == {size}, "reconciled registration owner size");
}}
'''


def msvc_number(value):
    """MSVC decorated positive number, used by compiler adjustor symbols."""
    if type(value) is not int or value < 0:
        raise ValueError('nonnegative adjustment magnitude required')
    if 1 <= value <= 10:
        return str(value-1)
    return ''.join(chr(ord('A')+int(c,16)) for c in f'{value:X}')+'@'


def emit(rva, size, offset, layout, layout_size):
    identifier(layout)
    if any(type(v) is not int or v <= 0 for v in (rva, size, offset, layout_size)):
        raise ValueError('positive member parameters required')
    cls = f'Adjustor{rva:x}'
    lead = prefix()+f'''// RVA 0x{rva:x}; {size} bytes
// Recipe: {RECIPE}
// {cls}, object: GUESS(low) STANDIN
// This derived type adds no storage and overrides its represented owner's destructor.
// Its external override and the referenced deletion helper are not reconstructed here.
// The global object requests ordinary compiler emission; initialization is not compared.
// Only the selected secondary adjustor is compared; a pass proves no original name.
// Origin: {json.dumps(origin(), sort_keys=True)}
'''
    header = lead+f'''#pragma once
#include "{layout}.h"
class {cls} : public ResearchLayouts::{layout} {{
public:
    ~{cls}() override;
}};
static_assert(sizeof({cls}) == {layout_size}, "represented owner layout");
'''
    return dict(cls=cls, header=header, source=lead+f'#include "{cls}.h"\nstatic {cls} object;\n',
                symbol=f'??_E{cls}@@W{msvc_number(offset)}EAAPEAXI@Z',
                callee=f'??_E{cls}@@UEAAPEAXI@Z')
