// NiRefObject functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-nirefobject
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x213be0, 50 bytes: NiRefObject::~NiRefObject
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <intrin.h>

#include "NiRefObject.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiRefObject::NiRefObject()
{
}

NiRefObject::~NiRefObject()
{
    // the object count is shared across threads, so the decrement must be atomic
    _InterlockedDecrement(&niRefObjectTotalCount);
}
