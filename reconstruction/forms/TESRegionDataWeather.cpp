// TESRegionDataWeather functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s14-tesregiondata-tesregiondataweather
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x253ea0, 20 bytes: TESRegionDataWeather::IsLoaded
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESRegionDataWeather.h"

bool TESRegionDataWeather::IsLoaded() const
{
    if (field18 != nullptr) {
        return true;
    }
    if (field10 != nullptr) {
        return true;
    }
    return false;
}
