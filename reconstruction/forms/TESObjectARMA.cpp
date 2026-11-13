// TESObjectARMA functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s06-tesobject-tesobjectarma
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x27d3f8, 9 bytes: TESObjectARMA::dtor
// Adapted bodies: TESObjectARMA::~TESObjectARMA, momusdigital/fnv_decomp@91e1b6e8,
// src/fallout_shared/tesobjectarma.cpp, no license grant.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectARMA.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESObjectARMA::TESObjectARMA()
{
}

TESObjectARMA::~TESObjectARMA()
{
}
