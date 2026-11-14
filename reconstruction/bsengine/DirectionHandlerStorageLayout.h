// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/D/DirectionHandler.h; GPL-3.0.
// DirectionHandler: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// DirectionHandlerLayout: GUESS(medium) STANDIN; represented layout type names
// Adapted from published p106 represented declaration reconstruction/bsengine/DirectionHandlerLayout.h.
// Include spelling and local type names changed; all represented fields, bases, size and offset assertions retained.
// DirectionHandlerStorageLayout: GUESS(medium) STANDIN; compilation-local represented type aliases.
#pragma once
#include <cstdint>
#include <cstddef>
#include "MenuEventHandlerStorageLayout.h"

namespace ResearchLayouts {
class DirectionHandlerStorageLayout : public MenuEventHandlerStorageLayout {
public:
    virtual ~DirectionHandlerStorageLayout();
    float nextRepeat;
    float menuKeyRepeatLong;
    float menuKeyRepeatShort;
    std::uint32_t repeatTimer;
    std::uint32_t currentRepeatCount;
    std::uint32_t longRepeatThresholdCount;
    bool repeatEnabled;
    bool unk29;
};
static_assert(sizeof(DirectionHandlerStorageLayout) == 48, "community represented size");
static_assert(offsetof(DirectionHandlerStorageLayout, nextRepeat) == 16, "nextRepeat offset");
static_assert(offsetof(DirectionHandlerStorageLayout, menuKeyRepeatLong) == 20, "menuKeyRepeatLong offset");
static_assert(offsetof(DirectionHandlerStorageLayout, menuKeyRepeatShort) == 24, "menuKeyRepeatShort offset");
static_assert(offsetof(DirectionHandlerStorageLayout, repeatTimer) == 28, "repeatTimer offset");
static_assert(offsetof(DirectionHandlerStorageLayout, currentRepeatCount) == 32, "currentRepeatCount offset");
static_assert(offsetof(DirectionHandlerStorageLayout, longRepeatThresholdCount) == 36, "longRepeatThresholdCount offset");
static_assert(offsetof(DirectionHandlerStorageLayout, repeatEnabled) == 40, "repeatEnabled offset");
static_assert(offsetof(DirectionHandlerStorageLayout, unk29) == 41, "unk29 offset");
}
