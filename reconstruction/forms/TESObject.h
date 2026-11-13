// TESObject declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s06-tesobject-tesobject
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm; its formType field sits at 0x1A.
// TESObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject::IsOcclusionMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// g_occlusionMarkerA, g_occlusionMarkerB, g_occlusionMarkerC: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESObject : public TESForm
{
public:
    virtual bool IsOcclusionMarker();  // compared: 0x275ee0
};

extern TESObject* g_occlusionMarkerA;
extern TESObject* g_occlusionMarkerB;
extern TESObject* g_occlusionMarkerC;
