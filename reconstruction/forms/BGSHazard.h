// BGSHazard declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgshazard
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSHazard: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject: STANDIN EXE_RTTI
// BGSHazard::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// hazardDefaultFloat: GUESS(low); the global at RVA 0x207A840
// unk20, hazard80, hazard88, hazard90, hazard94, hazard98, hazardA0, hazardA8, hazardB0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class TESObject : public TESForm
{
public:
};

class TESBoundObject : public TESObject
{
public:
};

class BGSHazard : public TESBoundObject
{
public:
    BGSHazard();
    virtual void InitializeData();  // compared: 0x261fc0

    std::uint8_t  unk20[0x60];   // 20
    std::uint64_t hazard80;      // 80
    std::uint64_t hazard88;      // 88
    float         hazard90;      // 90
    std::uint32_t hazard94;      // 94
    std::uint64_t hazard98;      // 98
    std::uint64_t hazardA0;      // A0
    std::uint64_t hazardA8;      // A8
    std::uint64_t hazardB0;      // B0
};

extern float hazardDefaultFloat;
