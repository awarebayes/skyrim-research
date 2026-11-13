// BSLightingShaderMaterialFacegen functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialfacegen
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1528e80, 52 bytes: BSLightingShaderMaterialFacegen::~BSLightingShaderMaterialFacegen (scalar deleting destructor)
//   RVA 0x1526760, 56 bytes: BSLightingShaderMaterialFacegen::Ctor
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <new>
#include "BSLightingShaderMaterialFacegen.h"

// Not compared on its own: Ctor below runs it in place, and the compiler emits the vftable here.
BSLightingShaderMaterialFacegen::BSLightingShaderMaterialFacegen()
{
    fieldA0 = 0;
    fieldA8 = 0;
    fieldB0 = 0;
}

BSLightingShaderMaterialFacegen* BSLightingShaderMaterialFacegen::Ctor()
{
    return new (this) BSLightingShaderMaterialFacegen();
}
