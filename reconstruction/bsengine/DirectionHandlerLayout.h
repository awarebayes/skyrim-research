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
#pragma once
#include <cstdint>
#include <cstddef>
#include "bsengine/MenuEventHandlerLayout.h"

namespace ResearchLayouts {
class DirectionHandlerLayout : public MenuEventHandlerLayout {
public:
    virtual ~DirectionHandlerLayout();
    float nextRepeat;
    float menuKeyRepeatLong;
    float menuKeyRepeatShort;
    std::uint32_t repeatTimer;
    std::uint32_t currentRepeatCount;
    std::uint32_t longRepeatThresholdCount;
    bool repeatEnabled;
    bool unk29;
};
static_assert(sizeof(DirectionHandlerLayout) == 48, "community represented size");
static_assert(offsetof(DirectionHandlerLayout, nextRepeat) == 16, "nextRepeat offset");
static_assert(offsetof(DirectionHandlerLayout, menuKeyRepeatLong) == 20, "menuKeyRepeatLong offset");
static_assert(offsetof(DirectionHandlerLayout, menuKeyRepeatShort) == 24, "menuKeyRepeatShort offset");
static_assert(offsetof(DirectionHandlerLayout, repeatTimer) == 28, "repeatTimer offset");
static_assert(offsetof(DirectionHandlerLayout, currentRepeatCount) == 32, "currentRepeatCount offset");
static_assert(offsetof(DirectionHandlerLayout, longRepeatThresholdCount) == 36, "longRepeatThresholdCount offset");
static_assert(offsetof(DirectionHandlerLayout, repeatEnabled) == 40, "repeatEnabled offset");
static_assert(offsetof(DirectionHandlerLayout, unk29) == 41, "unk29 offset");
}
