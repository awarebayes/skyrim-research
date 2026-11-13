// BSLightingShaderMaterialLODLandscape functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermateriallodlandscape
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1527fb0, 6 bytes: BSLightingShaderMaterialLODLandscape::GetFeature
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLightingShaderMaterialLODLandscape.h"

// TODO body: RVA 0x1527fb0, 6 bytes, BSLightingShaderMaterialLODLandscape::GetFeature.
BSShaderMaterial::Feature BSLightingShaderMaterialLODLandscape::GetFeature() const
{
    return static_cast<Feature>(0x12);
}
