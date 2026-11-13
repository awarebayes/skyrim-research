// BSSkyShaderProperty functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsskyshaderproperty
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1553540, 6 bytes: BSSkyShaderProperty::QShader
//   RVA 0x1553930, 8 bytes: BSSkyShaderProperty::GetBaseTexture
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSSkyShaderProperty.h"

std::int32_t BSSkyShaderProperty::QShader()
{
    return 10;
}

NiSourceTexture* BSSkyShaderProperty::GetBaseTexture()
{
    return unk98;
}
