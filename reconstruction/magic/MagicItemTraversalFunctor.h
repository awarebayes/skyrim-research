// MagicItemTraversalFunctor declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemtraversalfunctor
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// MagicItemTraversalFunctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// MagicItemTraversalFunctor::~MagicItemTraversalFunctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class MagicItemTraversalFunctor
{
public:
    MagicItemTraversalFunctor();
    virtual ~MagicItemTraversalFunctor();  // compared: 0x1527c0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(MagicItemTraversalFunctor) == 0x10, "MagicItemTraversalFunctor size");
