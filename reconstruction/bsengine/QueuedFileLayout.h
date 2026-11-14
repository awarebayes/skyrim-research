// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/Q/QueuedFile.h; GPL-3.0.
// QueuedFile: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// QueuedFileLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
#include <cstddef>
#include "bsengine/IOTaskLayout.h"
#include "bsengine/BSFixedStringLayout.h"

namespace ResearchLayouts {
class QueuedFileLayout;
class QueuedFileLayout : public IOTaskLayout {
public:
    virtual ~QueuedFileLayout();
    std::uint64_t unk18;
    NiPointerLayout<QueuedFileLayout> parent;
    std::uint64_t children;
    std::uint64_t unk30;
};
static_assert(sizeof(QueuedFileLayout) == 56, "community represented size");
static_assert(offsetof(QueuedFileLayout, unk18) == 24, "unk18 offset");
static_assert(offsetof(QueuedFileLayout, parent) == 32, "parent offset");
static_assert(offsetof(QueuedFileLayout, children) == 40, "children offset");
static_assert(offsetof(QueuedFileLayout, unk30) == 48, "unk30 offset");
}
