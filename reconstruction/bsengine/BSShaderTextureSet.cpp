// BSShaderTextureSet functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsshadertextureset
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x153b3c0, 9 bytes: BSShaderTextureSet::GetTexturePath
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSShaderTextureSet.h"

// Body done: RVA 0x153b3c0, 9 bytes, BSShaderTextureSet::GetTexturePath.
const char* BSShaderTextureSet::GetTexturePath(Texture a_texture)
{
    return texturePaths[a_texture];
}
