// BSDistantTreeShaderProperty functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsdistanttreeshaderproperty
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1558eb0, 8 bytes: BSDistantTreeShaderProperty::GetBaseTexture
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSDistantTreeShaderProperty.h"

// TODO body: RVA 0x1558eb0, 8 bytes, BSDistantTreeShaderProperty::GetBaseTexture.
NiSourceTexture* BSDistantTreeShaderProperty::GetBaseTexture()
{
    return baseTexture;
}
