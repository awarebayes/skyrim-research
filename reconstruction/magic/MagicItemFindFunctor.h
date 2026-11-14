// MagicItemFindFunctor declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemfindfunctor
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// MagicItemFindFunctor: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// MagicItemTraversalFunctor: STANDIN EXE_RTTI
// MagicItemFindFunctor::~MagicItemFindFunctor: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// MagicItemTraversalFunctor::~MagicItemTraversalFunctor, unknown08, unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class MagicItemTraversalFunctor
{
public:
    virtual ~MagicItemTraversalFunctor() = default;
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(MagicItemTraversalFunctor) == 0x10, "MagicItemTraversalFunctor size");

class MagicItemFindFunctor : public MagicItemTraversalFunctor
{
public:
    MagicItemFindFunctor();
    virtual ~MagicItemFindFunctor();  // compared: 0x152760 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(MagicItemFindFunctor) == 0x18, "MagicItemFindFunctor size");
