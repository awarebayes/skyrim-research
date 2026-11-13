// TESActorBase declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tesactorbase
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESActorBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject, TESBoundAnimObject: STANDIN EXE_RTTI
// TESActorBase::GetIsPlayerOwner: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESActorBase::IsAutoCalc, TESActorBase::SetAutoCalc, TESActorBase::~TESActorBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESActorBaseData::SetFlagBit: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
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
};

class TESBoundAnimObject : public TESBoundObject
{
public:
};

class TESActorBaseData
{
public:
    void SetFlagBit(std::uint32_t a_bit, bool a_value, bool a_unknown);
};

class TESActorBase : public TESBoundAnimObject
{
public:
    TESActorBase();
    virtual bool GetIsPlayerOwner() const;  // compared: 0x3b03a0
    virtual bool IsAutoCalc() const;  // compared: 0x3afed0
    virtual void SetAutoCalc(bool a_autoCalc);  // compared: 0x3afef0
    virtual ~TESActorBase();  // compared: 0x3cbc60 (scalar deleting destructor)

    std::uint8_t padding[0x130];
};
