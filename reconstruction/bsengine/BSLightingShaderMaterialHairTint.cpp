// BSLightingShaderMaterialHairTint functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialhairtint
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1528fb0, 52 bytes: BSLightingShaderMaterialHairTint::~BSLightingShaderMaterialHairTint (scalar deleting destructor)
//   RVA 0x1527050, 61 bytes: BSLightingShaderMaterialHairTint::Ctor
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <new>
#include "BSLightingShaderMaterialHairTint.h"

// Not compared on its own: Ctor below runs it in place, and the compiler emits the vftable here.
BSLightingShaderMaterialHairTint::BSLightingShaderMaterialHairTint()
{
    fieldA0 = g_hairTintDefaultA;
    fieldA8 = g_hairTintDefaultB;
}

BSLightingShaderMaterialHairTint* BSLightingShaderMaterialHairTint::Ctor()
{
    return new (this) BSLightingShaderMaterialHairTint();
}
