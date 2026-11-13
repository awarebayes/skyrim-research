// NiKeyBasedInterpolator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nikeybasedinterpolator
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf6e9f0, 62 bytes: NiKeyBasedInterpolator::~NiKeyBasedInterpolator
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiKeyBasedInterpolator.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiKeyBasedInterpolator::NiKeyBasedInterpolator()
{
}

// Body done: RVA 0xf6e9f0, 62 bytes, NiKeyBasedInterpolator::~NiKeyBasedInterpolator; compared as
// the scalar deleting destructor. The empty body lets the compiler inline the vftable store and
// the base destructor call into the deleting form.
NiKeyBasedInterpolator::~NiKeyBasedInterpolator()
{
}
