// BSLightingShaderMaterial functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterial
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x4b4a00, 52 bytes: BSLightingShaderMaterial::~BSLightingShaderMaterial (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLightingShaderMaterial.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared. The destructor itself stays undefined here so that
// the compiler calls the separate complete destructor, as the listing does.
BSLightingShaderMaterial::BSLightingShaderMaterial()
{
}
