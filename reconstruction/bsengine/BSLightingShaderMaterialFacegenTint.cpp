// BSLightingShaderMaterialFacegenTint functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialfacegentint
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1526fc0, 6 bytes: BSLightingShaderMaterialFacegenTint::GetFeature
//   RVA 0x1526e30, 48 bytes: BSLightingShaderMaterialFacegenTint::Ctor
//   RVA 0x1526f20, 60 bytes: BSLightingShaderMaterialFacegenTint::CopyMembers
//   RVA 0x1528ec0, 62 bytes: BSLightingShaderMaterialFacegenTint::~BSLightingShaderMaterialFacegenTint (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <new>
#include "BSLightingShaderMaterialFacegenTint.h"

// Not compared on its own: Ctor below runs it in place, and the compiler emits the vftable here.
BSLightingShaderMaterialFacegenTint::BSLightingShaderMaterialFacegenTint() :
    fieldA0{}, fieldA8(0)
{}

BSLightingShaderMaterialFacegenTint::Feature BSLightingShaderMaterialFacegenTint::GetFeature() const
{
    return static_cast<Feature>(5);
}

BSLightingShaderMaterialFacegenTint* BSLightingShaderMaterialFacegenTint::Ctor()
{
    return new (this) BSLightingShaderMaterialFacegenTint();
}

void BSLightingShaderMaterialFacegenTint::CopyMembers(BSShaderMaterial* a_other)
{
    BSLightingShaderMaterial::CopyMembers(a_other);
    const auto* other = static_cast<const BSLightingShaderMaterialFacegenTint*>(a_other);
    fieldA0 = other->fieldA0;
    fieldA8 = other->fieldA8;
}
