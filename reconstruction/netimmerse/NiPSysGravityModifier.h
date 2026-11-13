// NiPSysGravityModifier declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-nipsysgravitymodifier
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiPSysModifier.h for NiPSysModifier.
// NiPSysGravityModifier: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiPSysGravityModifier::LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// field30: GUESS(low)
// unknown38: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiPSysModifier.h"

class NiPSysGravityModifier : public NiPSysModifier
{
public:
    virtual void LinkObject(NiStream& a_stream);  // compared: 0xf9c400

    NiAVObject* field30;  // 30
    std::uint8_t unknown38[0x28];  // 38
};
static_assert(sizeof(NiPSysGravityModifier) == 0x60, "NiPSysGravityModifier size");
