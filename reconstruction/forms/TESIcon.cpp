// TESIcon functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesicon
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (Claude Haiku 5.5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1e85e0, 8 bytes: TESIcon::GetDefaultPath
//   RVA 0x1e85f0, 52 bytes: TESIcon::~TESIcon
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESIcon.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESIcon::TESIcon()
{
}

// GetDefaultPath: the listing returns the address of a fixed string.
const char* TESIcon::GetDefaultPath() const
{
    return "Textures";
}

// The destructor is declared only in the header: the target calls the complete destructor and then
// tests the delete flag, so attempt binds that call to its RVA (cookbook rule 18).
