// TESAmmo functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-tesammo
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x2695f0, 14 bytes: TESAmmo::GetPlayable
//   RVA 0x268ac0, 46 bytes: TESAmmo::InitializeData
//   RVA 0x2692c0, 46 bytes: TESAmmo::SaveGame
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESAmmo.h"

bool TESAmmo::GetPlayable() const
{
    return !TestBit(unk118[0], 1);
}

void TESAmmo::InitializeData()
{
    unk110 = 0;
    *reinterpret_cast<std::uint64_t*>(unk118) = 0;
    unkB8 = ammoDefault;
    InitializeSubobject(unk120, false);
}

void TESAmmo::SaveGame(BGSSaveFormBuffer* a_buf)
{
    TESForm::SaveGame(a_buf);
    SaveSubobject(unkA0, a_buf);
}
