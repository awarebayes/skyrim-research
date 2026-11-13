// BGSSceneActionPackage functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneactionpackage
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3ac610, 12 bytes: BGSSceneActionPackage::Unk_0B
//   RVA 0x3ac2b0, 29 bytes: BGSSceneActionPackage::Unk_11
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSSceneActionPackage.h"

void BGSSceneActionPackage::Unk_0B()
{
    RawAt<std::uint32_t>(this, 0x20) = 0;
    BGSSceneAction::Unk_0B();
}

void BGSSceneActionPackage::Unk_11()
{
    if (!Unk_05()) {
        flags14 |= 0x2;
    }
}
