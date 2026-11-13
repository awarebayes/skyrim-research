// BSLightingShaderMaterialParallaxOcc functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialparallaxocc
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1526170, 49 bytes: BSLightingShaderMaterialParallaxOcc::Ctor
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <new>

#include "BSLightingShaderMaterialParallaxOcc.h"

BSLightingShaderMaterialParallaxOcc::BSLightingShaderMaterialParallaxOcc()
{
}

// TODO body: RVA 0x1526170, 49 bytes, BSLightingShaderMaterialParallaxOcc::Ctor.
BSLightingShaderMaterialParallaxOcc* BSLightingShaderMaterialParallaxOcc::Ctor()
{
    new (this) BSLightingShaderMaterialParallaxOcc;
    unknownA0 = 0;
    unknownA8 = 0;
    return this;
}
