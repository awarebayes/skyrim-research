// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v3.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
// AutoRegisterCombatObject, CombatInventoryItemMagicT: EXE_RTTI
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
    AutoRegisterCombatObjectLayout();
    virtual ~AutoRegisterCombatObjectLayout();
};
static_assert(sizeof(AutoRegisterCombatObjectLayout<void>) == sizeof(void*), "fieldless registration base");
}
