// BSNavmesh declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s26-bsintrusiverefcounted-bsnavmesh
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSNavmesh: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSNavmesh::~BSNavmesh: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSNavmesh
{
public:
    BSNavmesh();
    virtual ~BSNavmesh();  // compared: 0x11e99f0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x110];  // 08
};
static_assert(sizeof(BSNavmesh) == 0x118, "BSNavmesh size");
