// NiStringExtraData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nistringextradata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xef71c0, 21 bytes: NiStringExtraData::IsEqual
//   RVA 0xef70e0, 43 bytes: NiStringExtraData::LoadBinary
//   RVA 0xef7130, 62 bytes: NiStringExtraData::RegisterStreamables
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiStringExtraData.h"

// TODO body: RVA 0xef71c0, 21 bytes, NiStringExtraData::IsEqual.
bool NiStringExtraData::IsEqual(NiObject* a_object)
{
    if (a_object != nullptr && value._data == static_cast<NiStringExtraData*>(a_object)->value._data) {
        return true;
    }
    return false;
}

// TODO body: RVA 0xef70e0, 43 bytes, NiStringExtraData::LoadBinary.
void NiStringExtraData::LoadBinary(NiStream& a_stream)
{
    NiExtraData::LoadBinary(a_stream);
    a_stream.LoadFixedString(value);
}

// TODO body: RVA 0xef7130, 62 bytes, NiStringExtraData::RegisterStreamables.
bool NiStringExtraData::RegisterStreamables(NiStream& a_stream)
{
    if (!NiExtraData::RegisterStreamables(a_stream)) {
        return false;
    }
    a_stream.RegisterFixedString(value);
    return true;
}
