// BSBloodSplatterShaderProperty functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsbloodsplattershaderproperty
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x152d8a0, 6 bytes: BSBloodSplatterShaderProperty::QShader
//   RVA 0x152db70, 8 bytes: BSBloodSplatterShaderProperty::GetBaseTexture
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSBloodSplatterShaderProperty.h"

std::int32_t BSBloodSplatterShaderProperty::QShader()
{
    return 12;
}

NiSourceTexture* BSBloodSplatterShaderProperty::GetBaseTexture()
{
    return unk88;
}
