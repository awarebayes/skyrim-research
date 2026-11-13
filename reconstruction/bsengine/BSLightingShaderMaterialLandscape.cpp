// BSLightingShaderMaterialLandscape functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermateriallandscape
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1527a80, 6 bytes: BSLightingShaderMaterialLandscape::GetFeature
//   RVA 0x1529030, 52 bytes: BSLightingShaderMaterialLandscape::~BSLightingShaderMaterialLandscape (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLightingShaderMaterialLandscape.h"

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared. The destructor itself stays undefined here so that the compiler
// calls the separate complete destructor, as the listing does.
BSLightingShaderMaterialLandscape::BSLightingShaderMaterialLandscape()
{
}

BSLightingShaderMaterialLandscape::Feature BSLightingShaderMaterialLandscape::GetFeature() const
{
    return static_cast<Feature>(0x13);
}
