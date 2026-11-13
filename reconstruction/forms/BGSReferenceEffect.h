// BGSReferenceEffect declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsreferenceeffect
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSReferenceEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSReferenceEffect::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class BGSReferenceEffect : public TESForm
{
public:
    virtual void InitializeData();  // compared: 0x29ec10

    // unknown20: GUESS(low)
    std::uint64_t unknown20;  // 20
    // unknown28: GUESS(low)
    std::uint64_t unknown28;  // 28
    // unknown30: GUESS(low)
    std::uint32_t unknown30;  // 30
};
