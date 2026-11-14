// BSIRagdollDriver declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsiragdolldriver
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSIRagdollDriver: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIRagdollDriver::~BSIRagdollDriver: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class BSIRagdollDriver
{
public:
    BSIRagdollDriver();
    virtual ~BSIRagdollDriver();  // compared: 0xbd9940 (scalar deleting destructor)
};
static_assert(sizeof(BSIRagdollDriver) == 0x8, "BSIRagdollDriver size");
