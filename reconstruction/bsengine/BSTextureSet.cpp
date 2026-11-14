// BSTextureSet functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bstextureset
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x32dfe0, 8 bytes: BSTextureSet::GetRTTI
//   RVA 0x32df90, 50 bytes: BSTextureSet::~BSTextureSet
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSTextureSet.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSTextureSet::BSTextureSet()
{
}

// Compared function: RVA 0x32dfe0, 8 bytes, BSTextureSet::GetRTTI.
const NiRTTI* BSTextureSet::GetRTTI() const
{
    return &NiRTTI_BSTextureSet;
}

// Body done: RVA 0x32df90, 50 bytes, BSTextureSet::~BSTextureSet; compared as the scalar deleting
// destructor. The target does the NiRefObject cleanup itself, so keep this empty definition and the
// constructor: the inline base destructors in the header make the compiler produce the same body.
BSTextureSet::~BSTextureSet()
{
}
