// TESTexture functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-testexture
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-4), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x146760, 3 bytes: TESTexture::GetMaxAllowedSize
//   RVA 0x1f2b20, 3 bytes: TESTexture::ClearDataComponent
//   RVA 0x1f3320, 8 bytes: TESTexture::GetDefaultPath
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESTexture.h"

// Body done: RVA 0x146760, 3 bytes, TESTexture::GetMaxAllowedSize.
std::uint32_t TESTexture::GetMaxAllowedSize()
{
    return 0;
}

// Body done: RVA 0x1f2b20, 3 bytes, TESTexture::ClearDataComponent.
void TESTexture::ClearDataComponent()
{
}

// Body done: RVA 0x1f3320, 8 bytes, TESTexture::GetDefaultPath.
const char* TESTexture::GetDefaultPath() const
{
    return "Textures\\";
}
