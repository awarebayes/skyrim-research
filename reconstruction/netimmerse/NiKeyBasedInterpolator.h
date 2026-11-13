// NiKeyBasedInterpolator declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nikeybasedinterpolator
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiInterpolator.h for NiInterpolator.
// NiKeyBasedInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiKeyBasedInterpolator::~NiKeyBasedInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiInterpolator.h"

class NiKeyBasedInterpolator : public NiInterpolator
{
public:
    NiKeyBasedInterpolator();
    virtual ~NiKeyBasedInterpolator();  // compared: 0xf6e9f0 (scalar deleting destructor)
};
static_assert(sizeof(NiKeyBasedInterpolator) == 0x18, "NiKeyBasedInterpolator size");
