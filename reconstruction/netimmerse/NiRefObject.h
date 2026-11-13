// NiRefObject declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-nirefobject
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiRefObject::~NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
// niRefObjectTotalCount: GUESS(low); the global count at RVA 0x331c620, bound by the unit's bind-hints.json
#pragma once

#include <cstdint>

extern "C" long niRefObjectTotalCount;

class NiRefObject
{
public:
    NiRefObject();
    virtual ~NiRefObject();  // compared: 0x213be0 (scalar deleting destructor)

    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");
