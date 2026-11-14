// BSInvMarker functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsinvmarker
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfff1d0, 62 bytes: BSInvMarker::~BSInvMarker
//   RVA 0xffed30, 4 bytes: BSInvMarker::CreateClone
//   RVA 0xfff210, 8 bytes: BSInvMarker::GetRTTI
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSInvMarker.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSInvMarker::BSInvMarker()
{
}


NiObject* BSInvMarker::CreateClone(NiCloningProcess&)
{
    return this;
}

const NiRTTI* BSInvMarker::GetRTTI() const
{
    return &NiRTTI_BSInvMarker;
}
