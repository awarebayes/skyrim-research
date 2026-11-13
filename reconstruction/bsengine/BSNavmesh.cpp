// BSNavmesh functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s26-bsintrusiverefcounted-bsnavmesh
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x11e99f0, 52 bytes: BSNavmesh::~BSNavmesh
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSNavmesh.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSNavmesh::BSNavmesh()
{
}

