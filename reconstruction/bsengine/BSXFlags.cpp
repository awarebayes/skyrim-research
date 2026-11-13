// BSXFlags functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bsxflags
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfd2da0, 4 bytes: BSXFlags::CreateClone
//   RVA 0xfd2de0, 19 bytes: BSXFlags::RegisterStreamables
//   RVA 0xfd30c0, 62 bytes: BSXFlags::~BSXFlags
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSXFlags.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSXFlags::BSXFlags()
{
}

// The clone is the object itself; the listing returns its first argument unchanged.
NiObject* BSXFlags::CreateClone(NiCloningProcess& a_cloning)
{
    return this;
}

// The listing calls the base stream check on this object and returns its negation.
// NiObject::StreamCanSkip: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the direct call to the base form is inferred from the listing
bool BSXFlags::RegisterStreamables(NiStream& a_stream)
{
    return !NiObject::StreamCanSkip();
}

// Compared as the scalar deleting destructor; the base destructor runs first, then the object is freed
// when the delete flag is set.
BSXFlags::~BSXFlags()
{
}
