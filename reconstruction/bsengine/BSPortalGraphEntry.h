// BSPortalGraphEntry declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsportalgraphentry
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiRefObject.h for NiRefObject.
// BSPortalGraphEntry: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSPortalGraphEntry::~BSPortalGraphEntry: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiRefObject.h"

class BSPortalGraphEntry : public NiRefObject
{
public:
    BSPortalGraphEntry();
    virtual ~BSPortalGraphEntry();  // compared: 0xfdb1f0 (scalar deleting destructor)

    std::uint8_t unknown10[0x130];  // 10
};
static_assert(sizeof(BSPortalGraphEntry) == 0x140, "BSPortalGraphEntry size");
