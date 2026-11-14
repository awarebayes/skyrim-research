// BGSHazard::InitializeData, build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgshazard
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 from the compared listing.
// Compared functions:
//   RVA 0x261fc0, 67 bytes: BGSHazard::InitializeData
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSHazard.h"

// Not compared: defined so that the compiler emits the vftable.


void BGSHazard::InitializeData()
{
    hazard80 = 0;
    hazard88 = 0;
    hazard90 = hazardDefaultFloat;
    hazard94 = 0;
    hazard98 = 0;
    hazardA0 = 0;
    hazardB0 = 0;
    hazardA8 = 0;
}
