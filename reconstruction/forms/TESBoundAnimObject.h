// TESBoundAnimObject declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-tesboundanimobject
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject: STANDIN EXE_RTTI
// TESBoundAnimObject::~TESBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESBoundObject::~TESBoundObject: GUESS(low)
// unknown20: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESObject : public TESForm
{
public:
};

class TESBoundObject : public TESObject
{
public:
    virtual ~TESBoundObject();
};

class TESBoundAnimObject : public TESBoundObject
{
public:
    TESBoundAnimObject();
    virtual ~TESBoundAnimObject() {}  // compared: 0x279140 (scalar deleting destructor)

    std::uint8_t unknown20[0x10];  // 20
};
static_assert(sizeof(TESBoundAnimObject) == 0x30, "TESBoundAnimObject size");
