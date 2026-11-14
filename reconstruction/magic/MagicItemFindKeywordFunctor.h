// MagicItemFindKeywordFunctor declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemfindkeywordfunctor
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// MagicItemFindKeywordFunctor: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// MagicItemTraversalFunctor, MagicItemFindFunctor: STANDIN EXE_RTTI
// MagicItemFindKeywordFunctor::~MagicItemFindKeywordFunctor: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// MagicItemTraversalFunctor::~MagicItemTraversalFunctor, unknown08, unknown10, unknown18: GUESS(low)
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
    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(MagicItemFindFunctor) == 0x18, "MagicItemFindFunctor size");

class MagicItemFindKeywordFunctor : public MagicItemFindFunctor
{
public:
    MagicItemFindKeywordFunctor();
    virtual ~MagicItemFindKeywordFunctor();  // compared: 0x152790 (scalar deleting destructor)

    // members: padding kept; only the destructor is compared
    std::uint8_t unknown18[0x8];  // 18
};
static_assert(sizeof(MagicItemFindKeywordFunctor) == 0x20, "MagicItemFindKeywordFunctor size");
