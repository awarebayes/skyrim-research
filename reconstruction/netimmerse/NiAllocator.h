// NiAllocator declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-niallocator
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// NiAllocator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiAllocator::~NiAllocator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class NiAllocator
{
public:
    NiAllocator();
    virtual ~NiAllocator();  // compared: 0xeae960 (scalar deleting destructor)
};
static_assert(sizeof(NiAllocator) == 0x8, "NiAllocator size");
