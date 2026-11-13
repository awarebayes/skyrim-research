// TESObjectCONT functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tesobjectcont
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x281530, 24 bytes: TESObjectCONT::InitializeData
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectCONT.h"

void TESObjectCONT::InitializeData()
{
    unkB9 = 0;
    unkC0 = 0;
    unkC8 = 0;
}
