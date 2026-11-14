// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v2.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
// AutoRegisterCombatMagicCaster, CombatMagicCasterBoundItem: EXE_RTTI
// AutoRegisterCombatMagicCasterBoundItemLayout: GUESS(medium) STANDIN; layout-only spelling for the RTTI specialization
// RTTI lists each product specialization as a distinct nonvirtual direct base.
// Each base size is independently reconciled; the owner allocation size is checked.
#pragma once
#include "AutoRegisterCombatObjectLayout.h"
namespace ResearchLayouts {
class CombatMagicCasterBoundItem;
class AutoRegisterCombatMagicCasterBoundItemLayout :
    public AutoRegisterCombatObjectLayout<CombatMagicCasterBoundItem>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemMagic, CombatMagicCasterBoundItem>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemShout, CombatMagicCasterBoundItem>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemStaff, CombatMagicCasterBoundItem>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemPotion, CombatMagicCasterBoundItem>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemScroll, CombatMagicCasterBoundItem>> {
public:
    ~AutoRegisterCombatMagicCasterBoundItemLayout() override;
};
static_assert(sizeof(AutoRegisterCombatMagicCasterBoundItemLayout) == 48, "reconciled registration owner size");
}
