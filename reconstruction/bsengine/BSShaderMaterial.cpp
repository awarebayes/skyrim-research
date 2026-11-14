// BSShaderMaterial functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s19-bsshadermaterial-bsshadermaterial
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1575700, 41 bytes: BSShaderMaterial::CopyMembers
//   RVA 0x15758f0, 43 bytes: BSShaderMaterial::~BSShaderMaterial (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSShaderMaterial.h"

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared.
BSShaderMaterial::BSShaderMaterial()
{
}

BSShaderMaterial::Feature BSShaderMaterial::GetFeature() const
{
    return Feature::kDefault;
}

BSShaderMaterial::Type BSShaderMaterial::GetType() const
{
    return static_cast<Type>(0);
}

BSShaderMaterial* BSShaderMaterial::GetDefault()
{
    return gDefaultShaderMaterial;
}

void BSShaderMaterial::CopyMembers(BSShaderMaterial* a_other)
{
    RawAt<BSShaderPair>(this, 0x0c) = RawAt<BSShaderPair>(a_other, 0x0c);
    RawAt<BSShaderPair>(this, 0x14) = RawAt<BSShaderPair>(a_other, 0x14);
    RawAt<BSShaderPair>(this, 0x1c) = RawAt<BSShaderPair>(a_other, 0x1c);
    RawAt<BSShaderPair>(this, 0x24) = RawAt<BSShaderPair>(a_other, 0x24);
}
