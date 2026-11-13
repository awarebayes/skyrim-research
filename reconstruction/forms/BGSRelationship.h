// BGSRelationship declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsrelationship
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSRelationship: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSRelationship::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class BGSRelationship : public TESForm
{
public:
    virtual void InitializeData();  // compared: 0x3a46b0

    // unk20, unk28, unk30, unk38: GUESS(low)
    void*         unk20;  // 20
    void*         unk28;  // 28
    void*         unk30;  // 30
    std::uint32_t unk38;  // 38
};
