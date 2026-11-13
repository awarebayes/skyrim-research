// NiBooleanExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-nibooleanextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiBooleanExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiBooleanExtraData::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiExtraData.h"

class NiBooleanExtraData : public NiExtraData
{
public:
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xf0ff60

    bool value;  // 18
    std::uint8_t unknown19[0x7];  // 19
};
static_assert(sizeof(NiBooleanExtraData) == 0x20, "NiBooleanExtraData size");
