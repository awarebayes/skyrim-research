// BSWindModifier declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswindmodifier
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiPSysModifier.h for NiPSysModifier.
// BSWindModifier: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSWindModifier::GetRTTI, BSWindModifier::~BSWindModifier: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiPSysModifier.h"

class NiRTTI;

class BSWindModifier : public NiPSysModifier
{
public:
    BSWindModifier();
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xfd8f90
    virtual ~BSWindModifier();  // compared: 0xfd8f50 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown30[0x8];  // 30
};
static_assert(sizeof(BSWindModifier) == 0x38, "BSWindModifier size");
