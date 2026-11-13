// BSFogProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsfogproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObjectNET.h for NiObjectNET.
// BSFogProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiProperty, NiFogProperty: STANDIN EXE_RTTI
// BSFogProperty::~BSFogProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiFogProperty::~NiFogProperty: GUESS(low)
// unknown30, unknown50: GUESS(low)
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
    virtual ~NiFogProperty();

    std::uint8_t unknown30[0x20];  // 30
};
static_assert(sizeof(NiFogProperty) == 0x50, "NiFogProperty size");

class BSFogProperty : public NiFogProperty
{
public:
    BSFogProperty();
    virtual ~BSFogProperty() {}  // compared: 0x155c460 (scalar deleting destructor)

    std::uint8_t unknown50[0x40];  // 50
};
static_assert(sizeof(BSFogProperty) == 0x90, "BSFogProperty size");
