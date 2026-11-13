// NiFloatExtraData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nifloatextradata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/o2-fpfast.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf10f90, 22 bytes: NiFloatExtraData::IsEqual
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiFloatExtraData.h"

// Body done: RVA 0xf10f90, 22 bytes, NiFloatExtraData::IsEqual. The null test comes first, so the
// other object's value is read only after it.
bool NiFloatExtraData::IsEqual(NiObject* a_object)
{
    if (a_object == nullptr) {
        return false;
    }
    auto* other = static_cast<NiFloatExtraData*>(a_object);
    return value == other->value;
}
