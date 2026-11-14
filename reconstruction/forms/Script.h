// Script declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-script
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// Script: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Script::InitItemImpl, Script::GetProcessScripts: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class Script : public TESForm
{
public:
    virtual void InitItemImpl();  // compared: 0x344760
    static bool GetProcessScripts();  // compared: 0x3463a0
};
