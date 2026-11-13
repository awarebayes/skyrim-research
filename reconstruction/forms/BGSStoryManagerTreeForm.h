// BGSStoryManagerTreeForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsstorymanagertreeform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSStoryManagerTreeForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSStoryManagerTreeForm::~BGSStoryManagerTreeForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class BGSStoryManagerTreeForm;

class BGSStoryManagerTreeForm : public TESForm
{
public:
    BGSStoryManagerTreeForm();
    virtual ~BGSStoryManagerTreeForm();  // compared: 0x1c72c0 (scalar deleting destructor)
    // BGSStoryManagerTreeForm::GetChild, BGSStoryManagerTreeForm::QChildCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x1c7ce0, 0x1c8510
    virtual BGSStoryManagerTreeForm* GetChild(std::uint32_t a_idx) const;  // compared: 0x1c7ce0
    virtual std::uint32_t QChildCount() const;  // compared: 0x1c8510
    // unknown20: GUESS(low)
    std::uint8_t unknown20[0x8];
};
