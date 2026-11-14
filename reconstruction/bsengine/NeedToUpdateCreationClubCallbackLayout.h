// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/N/NeedToUpdateCreationClubCallback.h; GPL-3.0.
// NeedToUpdateCreationClubCallback: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// NeedToUpdateCreationClubCallbackLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
#include <cstddef>
#include "bsengine/IMessageBoxCallbackLayout.h"

namespace ResearchLayouts {
class NeedToUpdateCreationClubCallbackLayout : public IMessageBoxCallbackLayout {
public:
    virtual ~NeedToUpdateCreationClubCallbackLayout();
};
static_assert(sizeof(NeedToUpdateCreationClubCallbackLayout) == 16, "community represented size");
}
