// BSInvMarker declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsinvmarker
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// BSInvMarker: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSInvMarker::~BSInvMarker, BSInvMarker::CreateClone, BSInvMarker::GetRTTI: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown18: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiExtraData.h"

// NiRTTI_BSInvMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the RTTI global at RVA 0x332fe58, bound by hint
// base destructor at RVA 0xef9b00 is bound by hint under a guessed name
extern NiRTTI NiRTTI_BSInvMarker;

class BSInvMarker : public NiExtraData
{
public:
    BSInvMarker();
    virtual ~BSInvMarker() {}  // compared: 0xfff1d0 (scalar deleting destructor, inline stand-in)
    virtual NiObject* CreateClone(NiCloningProcess& a_cloning);  // compared: 0xffed30
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xfff210

    std::uint8_t unknown18[0x10];  // 18
};
static_assert(sizeof(BSInvMarker) == 0x28, "BSInvMarker size");
