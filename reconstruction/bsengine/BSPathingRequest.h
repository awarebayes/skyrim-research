// BSPathingRequest declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bspathingrequest
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSPathingRequest: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSPathingRequest::CheckValid: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSPathingRequest
{
public:
    virtual void CheckValid();  // compared: 0x11cbe10

    // members: padding kept; only CheckValid is compared
    std::uint8_t unknown08[0xF8];  // 08
};
static_assert(sizeof(BSPathingRequest) == 0x100, "BSPathingRequest size");
