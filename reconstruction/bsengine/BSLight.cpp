// BSLight functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bslight
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (Claude Haiku 5.5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1578880, 3 bytes: BSLight::Unk_03
//   RVA 0x1578840, 52 bytes: BSLight::~BSLight
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLight.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSLight::BSLight()
{
}

// Unk_03: the listing returns false.
bool BSLight::Unk_03()
{
    return false;
}

// The destructor is declared only in the header: the target calls the complete destructor and then
// tests the delete flag, so attempt binds that call to its RVA (cookbook rule 18).
