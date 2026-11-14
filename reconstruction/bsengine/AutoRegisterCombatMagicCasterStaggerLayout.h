// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v2.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
// AutoRegisterCombatMagicCaster, CombatMagicCasterStagger: EXE_RTTI
// AutoRegisterCombatMagicCasterStaggerLayout: GUESS(medium) STANDIN; layout-only spelling for the RTTI specialization
// RTTI lists each product specialization as a distinct nonvirtual direct base.
// Each base size is independently reconciled; the owner allocation size is checked.
#pragma once
#include "AutoRegisterCombatObjectLayout.h"
namespace ResearchLayouts {
class CombatMagicCasterStagger;
class AutoRegisterCombatMagicCasterStaggerLayout :
    public AutoRegisterCombatObjectLayout<CombatMagicCasterStagger>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemMagic, CombatMagicCasterStagger>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemShout, CombatMagicCasterStagger>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemStaff, CombatMagicCasterStagger>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemPotion, CombatMagicCasterStagger>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemScroll, CombatMagicCasterStagger>> {
public:
    ~AutoRegisterCombatMagicCasterStaggerLayout() override;
};
static_assert(sizeof(AutoRegisterCombatMagicCasterStaggerLayout) == 48, "reconciled registration owner size");
}
