// NiAlphaAccumulator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-nialphaaccumulator
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf0f290, 19 bytes: NiAlphaAccumulator::IsEqual
//   RVA 0xf0f4a0, 62 bytes: NiAlphaAccumulator::~NiAlphaAccumulator
// Adapted bodies: NiAlphaAccumulator::~NiAlphaAccumulator, momusdigital/fnv_decomp@91e1b6e8
// src/gamebryo2.2/corelibs/nimain/nialphaaccumulator.cpp:562, no licence (maintainer-authorized sibling;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiAlphaAccumulator.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiAlphaAccumulator::NiAlphaAccumulator()
{
}

// TODO body: RVA 0xf0f290, 19 bytes, NiAlphaAccumulator::IsEqual.
bool NiAlphaAccumulator::IsEqual(NiObject* a_object)
{
    return NiBackToFrontAccumulator::IsEqual(a_object) != false;
}

// TODO body: RVA 0xf0f4a0, 62 bytes, NiAlphaAccumulator::~NiAlphaAccumulator; compared as the
// scalar deleting destructor. If the target calls a separate destructor, keep only the declaration
// and delete this definition (cookbook rule 18).
NiAlphaAccumulator::~NiAlphaAccumulator()
{
}
