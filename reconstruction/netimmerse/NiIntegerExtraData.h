// NiIntegerExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-niintegerextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiIntegerExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiIntegerExtraData::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiExtraData.h"

class NiIntegerExtraData : public NiExtraData
{
public:
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xf121e0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint32_t value;  // 18
    std::uint8_t unknown1C[0x4];  // 1C
};
static_assert(sizeof(NiIntegerExtraData) == 0x20, "NiIntegerExtraData size");
