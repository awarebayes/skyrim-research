// NiIntegersExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-niintegersextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiIntegersExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiIntegersExtraData::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown18: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiExtraData.h"

class NiIntegersExtraData : public NiExtraData
{
public:
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xf12b50

    // members: padding kept; only GetRTTI is compared
    std::uint8_t unknown18[0x10];  // 18
};
static_assert(sizeof(NiIntegersExtraData) == 0x28, "NiIntegersExtraData size");
