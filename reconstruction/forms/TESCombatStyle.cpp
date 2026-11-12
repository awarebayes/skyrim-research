// TESCombatStyle::InitItemImpl and ~TESCombatStyle, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x26a160, 18 bytes (InitItemImpl).
// RVA 0x26a890, 62 bytes (scalar deleting destructor of TESCombatStyle).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The destructor is compared.
// InitItemImpl is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "TESCombatStyle.h"

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
TESCombatStyle::TESCombatStyle()
{
}

TESCombatStyle::~TESCombatStyle()
{
}

void TESCombatStyle::InitItemImpl()
{
    if (!TestBit(formFlags, 3)) {
        SetFormHelper(this, true);
    }
}
