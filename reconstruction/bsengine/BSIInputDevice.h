// BSIInputDevice declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsiinputdevice
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSIInputDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIInputDevice::~BSIInputDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class BSIInputDevice
{
public:
    BSIInputDevice();
    virtual ~BSIInputDevice() {}  // compared: 0xcfc0b0 (scalar deleting destructor)
};
static_assert(sizeof(BSIInputDevice) == 0x8, "BSIInputDevice size");
