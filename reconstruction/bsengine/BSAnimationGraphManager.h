// BSAnimationGraphManager declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsanimationgraphmanager
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSAnimationGraphManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSTEventSink_UBSAnimationGraphEvent: STANDIN EXE_RTTI
// BSAnimationGraphManager::~BSAnimationGraphManager: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// BSTEventSink_UBSAnimationGraphEvent::~BSTEventSink_UBSAnimationGraphEvent, unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSTEventSink_UBSAnimationGraphEvent
{
public:
    virtual ~BSTEventSink_UBSAnimationGraphEvent() = default;
};
static_assert(sizeof(BSTEventSink_UBSAnimationGraphEvent) == 0x8, "BSTEventSink_UBSAnimationGraphEvent size");

class BSAnimationGraphManager : public BSTEventSink_UBSAnimationGraphEvent
{
public:
    BSAnimationGraphManager();
    virtual ~BSAnimationGraphManager();  // compared: 0xbc3c30 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0xB0];  // 08
};
static_assert(sizeof(BSAnimationGraphManager) == 0xB8, "BSAnimationGraphManager size");
