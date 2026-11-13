// TESRegionData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s14-tesregiondata-tesregiondata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x24fee0, 29 bytes: TESRegionData::LoadDataHeader
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESRegionData.h"

bool TESRegionData::LoadDataHeader(void* a_arg1)
{
    if (a_arg1 == nullptr) {
        return false;
    }
    const auto* src = static_cast<const std::uint8_t*>(a_arg1);
    unk08 = src[4];
    const std::uint8_t priority = src[5];
    if (priority <= 100) {
        unk0A = priority;
    }
    return true;
}
