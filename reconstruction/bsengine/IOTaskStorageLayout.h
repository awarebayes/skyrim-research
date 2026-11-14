// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/I/IOTask.h; GPL-3.0.
// IOTask: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// IOTaskLayout: GUESS(medium) STANDIN; represented layout type names
// Adapted from published p106 represented declaration reconstruction/bsengine/IOTaskLayout.h.
// Include spelling and local type names changed; all represented fields, bases, size and offset assertions retained.
// IOTaskStorageLayout: GUESS(medium) STANDIN; compilation-local represented type aliases.
#pragma once
#include <cstdint>
#include <cstddef>
#include "BSTaskStorageLayout.h"

namespace ResearchLayouts {
class IOTaskStorageLayout : public BSTaskStorageLayout {
public:
    virtual ~IOTaskStorageLayout();
};
static_assert(sizeof(IOTaskStorageLayout) == 24, "community represented size");
}
