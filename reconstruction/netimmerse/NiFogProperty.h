// NiFogProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-nifogproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObjectNET.h for NiObjectNET.
// NiFogProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiProperty: STANDIN EXE_RTTI
// NiFogProperty::~NiFogProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObjectNET.h"

class NiProperty : public NiObjectNET
{
public:
};
static_assert(sizeof(NiProperty) == 0x30, "NiProperty size");

class NiFogProperty : public NiProperty
{
public:
    NiFogProperty();
    virtual ~NiFogProperty();  // compared: 0xf11f90 (scalar deleting destructor); declared only, rule 18

    std::uint8_t unknown30[0x20];  // 30
};
static_assert(sizeof(NiFogProperty) == 0x50, "NiFogProperty size");
