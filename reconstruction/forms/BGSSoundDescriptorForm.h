// BGSSoundDescriptorForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgssounddescriptorform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSSoundDescriptorForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSSoundDescriptorForm::SetFormEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class BGSSoundDescriptorForm : public TESForm
{
public:
    virtual bool SetFormEditorID(const char* a_str);  // compared: 0x32a7c0
};
