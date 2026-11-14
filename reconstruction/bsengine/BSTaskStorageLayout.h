// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/B/BSTask.h; GPL-3.0.
// BSTask: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// BSTaskLayout: GUESS(medium) STANDIN; represented layout type names
// Adapted from published p106 represented declaration reconstruction/bsengine/BSTaskLayout.h.
// Include spelling and local type names changed; all represented fields, bases, size and offset assertions retained.
// BSTaskStorageLayout: GUESS(medium) STANDIN; compilation-local represented type aliases.
#pragma once
#include <cstdint>
#include <cstddef>

namespace ResearchLayouts {
class BSTaskStorageLayout {
public:
    virtual ~BSTaskStorageLayout();
    volatile std::int32_t refCount;
    std::uint32_t unk0C;
    std::uint64_t unk10;
};
static_assert(sizeof(BSTaskStorageLayout) == 24, "community represented size");
static_assert(offsetof(BSTaskStorageLayout, refCount) == 8, "refCount offset");
static_assert(offsetof(BSTaskStorageLayout, unk0C) == 12, "unk0C offset");
static_assert(offsetof(BSTaskStorageLayout, unk10) == 16, "unk10 offset");
}
