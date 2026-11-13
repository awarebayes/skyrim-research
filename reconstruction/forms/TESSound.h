// TESSound declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tessound
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESSound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject, TESBoundAnimObject: STANDIN EXE_RTTI
// TESSound::Clone3D, TESSound::InitializeData, TESSound::SetFormEditorID, TESSound::~TESSound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
// NiAVObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class NiAVObject;

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

class TESSound : public TESBoundAnimObject
{
public:
    TESSound();
    virtual NiAVObject* Clone3D(TESObjectREFR* a_ref);  // compared: 0x388860
    virtual void InitializeData();  // compared: 0x388880
    virtual bool SetFormEditorID(const char* a_str);  // compared: 0x388620
    virtual ~TESSound();  // compared: 0x3888d0 (scalar deleting destructor)

    std::uint8_t unknown20[0x10];  // 20
    void* unknown30;  // 30
};
