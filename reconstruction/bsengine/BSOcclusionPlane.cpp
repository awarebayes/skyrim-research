// BSOcclusionPlane functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsocclusionplane
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfe9bd0, 50 bytes: BSOcclusionPlane::~BSOcclusionPlane
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSOcclusionPlane.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSOcclusionPlane::BSOcclusionPlane()
{
}

// Body done: RVA 0xfe9bd0, 50 bytes, BSOcclusionPlane::~BSOcclusionPlane; compared as the scalar
// deleting destructor. The target does the NiRefObject cleanup itself, so keep this empty
// definition and the constructor: the inline base destructors in the header make the compiler
// produce the same body.
BSOcclusionPlane::~BSOcclusionPlane()
{
}
