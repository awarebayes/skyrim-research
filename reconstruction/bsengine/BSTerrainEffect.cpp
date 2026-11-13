// BSTerrainEffect functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsterraineffect
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x4b7c40, 5 bytes: BSTerrainEffect::GetManagerHandlesSaveLoad
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSTerrainEffect.h"

// Reads the base class flag at 0x24 that the target loads; what the flag means is not verified here.
bool BSTerrainEffect::GetManagerHandlesSaveLoad() const
{
    return initialized;
}
