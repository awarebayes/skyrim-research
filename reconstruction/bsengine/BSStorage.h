// BSStorage declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s26-bsintrusiverefcounted-bsstorage
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSStorage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSStorage::~BSStorage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSStorage
{
public:
    BSStorage();
    virtual ~BSStorage();  // compared: 0x1e7740 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x18];  // 08
};
static_assert(sizeof(BSStorage) == 0x20, "BSStorage size");
