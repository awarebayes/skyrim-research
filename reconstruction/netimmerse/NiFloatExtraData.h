// NiFloatExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nifloatextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiFloatExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiFloatExtraData::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown1C: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiExtraData.h"

class NiFloatExtraData : public NiExtraData
{
public:
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xf10f90

    // members
    float value;  // 18
    std::uint8_t unknown1C[0x4];  // 1C
};
static_assert(sizeof(NiFloatExtraData) == 0x20, "NiFloatExtraData size");
