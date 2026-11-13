// NiGeometryData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nigeometrydata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObject.h for NiObject.
// NiGeometryData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiGeometryData::GetActiveVertexCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// activeVertexCount: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObject.h"

class NiGeometryData : public NiObject
{
public:
    virtual std::uint16_t GetActiveVertexCount() const;  // compared: 0xefbff0

    std::uint16_t activeVertexCount;  // 10
    std::uint8_t unknown12[0x56];  // 12
};
static_assert(sizeof(NiGeometryData) == 0x68, "NiGeometryData size");
