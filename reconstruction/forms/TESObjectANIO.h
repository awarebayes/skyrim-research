// TESObjectANIO declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesobjectanio
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESObjectANIO: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectANIO::GetFormEditorID, TESObjectANIO::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

// g_defaultFormEditorIDString: GUESS(low); the default string address in .rdata used by GetFormEditorID
extern const char g_defaultFormEditorIDString[];

class TESObjectANIO : public TESForm
{
public:
    virtual const char* GetFormEditorID() const;  // compared: 0x27bb70

    // unknown20: GUESS(low); the helper of InitItemImpl receives this + 0x20
    std::uint8_t unknown20[0x38];  // 20
    // editorID: GUESS(low)
    // editorID is read by GetFormEditorID; a null value falls back to a default string
    const char* editorID;  // 58
};
