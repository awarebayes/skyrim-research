// NiStringsExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nistringsextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiStringsExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiStringsExtraData::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown18: GUESS(low)
// NiRTTI_NiStringsExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); RTTI object bound by hint to its data address
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiExtraData.h"

extern NiRTTI NiRTTI_NiStringsExtraData;

class NiStringsExtraData : public NiExtraData
{
public:
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xeeeec0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown18[0x10];  // 18
};
static_assert(sizeof(NiStringsExtraData) == 0x28, "NiStringsExtraData size");
