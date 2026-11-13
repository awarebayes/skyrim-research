// BGSIdleMarker declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-bgsidlemarker
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSIdleMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject: STANDIN EXE_RTTI
// BGSIdleMarker::GetIgnoredBySandbox: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class BGSIdleMarker : public TESBoundObject
{
public:
    virtual bool GetIgnoredBySandbox() const;  // compared: 0x391b80

    // unknown20: GUESS(low)
    std::uint8_t unknown20[0x40];  // 20
    // unknown60: GUESS(low)
    std::uint8_t unknown60;  // 60
};
