// BSShadowParabolicLight functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsshadowparaboliclight
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1588e20, 11 bytes: BSShadowParabolicLight::GetIsOmniLight
//   RVA 0x1588d50, 31 bytes: BSShadowParabolicLight::ReturnShadowmaps
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSShadowParabolicLight.h"

// TODO body: RVA 0x1588e20, 11 bytes, BSShadowParabolicLight::GetIsOmniLight.
bool BSShadowParabolicLight::GetIsOmniLight()
{
    return state140 == 2;
}

// TODO body: RVA 0x1588d50, 31 bytes, BSShadowParabolicLight::ReturnShadowmaps.
void BSShadowParabolicLight::ReturnShadowmaps()
{
    if (state140 == 2) {
        shadowmap148->state144 = 0xffffffff;
    }
    return ReturnShadowmapsTarget();
}
