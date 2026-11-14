// BSISoundDescriptor declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsisounddescriptor
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSISoundDescriptor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSISoundDescriptor::~BSISoundDescriptor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class BSISoundDescriptor
{
public:
    BSISoundDescriptor();
    virtual ~BSISoundDescriptor() {}  // compared: 0x32ac50 (scalar deleting destructor)
};
static_assert(sizeof(BSISoundDescriptor) == 0x8, "BSISoundDescriptor size");
