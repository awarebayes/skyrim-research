// BGSPickupPutdownSounds functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgspickupputdownsounds
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (Claude Haiku 5.5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1db710, 3 bytes: BGSPickupPutdownSounds::ClearDataComponent
//   RVA 0x1db6f0, 11 bytes: BGSPickupPutdownSounds::InitializeDataComponent
//   RVA 0x1db880, 43 bytes: BGSPickupPutdownSounds::~BGSPickupPutdownSounds
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSPickupPutdownSounds.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSPickupPutdownSounds::BGSPickupPutdownSounds()
{
}

// ClearDataComponent: the listing is a bare return; there is no work to do.
void BGSPickupPutdownSounds::ClearDataComponent()
{
}

// InitializeDataComponent: both qwords are zeroed, in the same order as the listing.
void BGSPickupPutdownSounds::InitializeDataComponent()
{
    field08 = 0;
    field10 = 0;
}

// Compared as the scalar deleting destructor; the base destructor and vftable store are inlined by the
// compiler, so the body is empty.
BGSPickupPutdownSounds::~BGSPickupPutdownSounds()
{
}
