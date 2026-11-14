// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v2.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
// AutoRegisterCombatMagicCaster, CombatMagicCasterRestore: EXE_RTTI
// AutoRegisterCombatMagicCasterRestoreLayout: GUESS(medium) STANDIN; layout-only spelling for the RTTI specialization
// RTTI lists each product specialization as a distinct nonvirtual direct base.
// Each base size is independently reconciled; the owner allocation size is checked.
#pragma once
#include "AutoRegisterCombatObjectLayout.h"
namespace ResearchLayouts {
class CombatMagicCasterRestore;
class AutoRegisterCombatMagicCasterRestoreLayout :
    public AutoRegisterCombatObjectLayout<CombatMagicCasterRestore>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemMagic, CombatMagicCasterRestore>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemShout, CombatMagicCasterRestore>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemStaff, CombatMagicCasterRestore>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemPotion, CombatMagicCasterRestore>>,
    public AutoRegisterCombatObjectLayout<CombatInventoryItemMagicT<CombatInventoryItemScroll, CombatMagicCasterRestore>> {
public:
    ~AutoRegisterCombatMagicCasterRestoreLayout() override;
};
static_assert(sizeof(AutoRegisterCombatMagicCasterRestoreLayout) == 48, "reconciled registration owner size");
}
