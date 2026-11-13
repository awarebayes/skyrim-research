// BGSVoiceType declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsvoicetype
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSVoiceType::SetFormEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

// FormEditorIDSet: GUESS(low); the callee at RVA 0x10d710, bound by the unit's bind-hints.json
void FormEditorIDSet(void* a_dest, const char* a_str, bool a_flag);

class BGSVoiceType : public TESForm
{
public:
    virtual bool SetFormEditorID(const char* a_str);  // compared: 0x3aee30

    // unknown20, unk28: GUESS(low)
    std::uint8_t unknown20[0x8];  // 20
    std::uint8_t unk28[0x8];      // 28
};
