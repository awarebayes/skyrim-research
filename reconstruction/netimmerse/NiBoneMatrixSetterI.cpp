// NiBoneMatrixSetterI functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nibonematrixsetteri
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-4 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x15797a0, 43 bytes: NiBoneMatrixSetterI::~NiBoneMatrixSetterI
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiBoneMatrixSetterI.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiBoneMatrixSetterI::NiBoneMatrixSetterI()
{
}

// RVA 0x15797a0, 43 bytes, NiBoneMatrixSetterI::~NiBoneMatrixSetterI: the target inlines the complete
// destructor (vftable store, then class-scope delete), so the destructor is an empty inline body in
// the header.
