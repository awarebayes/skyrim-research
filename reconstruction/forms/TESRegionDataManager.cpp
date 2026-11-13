// TESRegionDataManager functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s36-tesregiondatamanager-tesregiondatamanager
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x251870, 45 bytes: TESRegionDataManager::AsRegionDataObjects
//   RVA 0x2518b0, 45 bytes: TESRegionDataManager::AsRegionDataWeather
//   RVA 0x2518f0, 45 bytes: TESRegionDataManager::AsRegionDataMap
//   RVA 0x251930, 45 bytes: TESRegionDataManager::AsRegionDataLandscape
//   RVA 0x251970, 45 bytes: TESRegionDataManager::AsRegionDataGrass
//   RVA 0x2519b0, 45 bytes: TESRegionDataManager::AsRegionDataSound
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESRegionDataManager.h"

TESRegionDataObjects* TESRegionDataManager::AsRegionDataObjects(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 2) {
        return reinterpret_cast<TESRegionDataObjects*>(a_data);
    }
    return nullptr;
}

TESRegionDataWeather* TESRegionDataManager::AsRegionDataWeather(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 3) {
        return reinterpret_cast<TESRegionDataWeather*>(a_data);
    }
    return nullptr;
}

TESRegionDataMap* TESRegionDataManager::AsRegionDataMap(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 4) {
        return reinterpret_cast<TESRegionDataMap*>(a_data);
    }
    return nullptr;
}

TESRegionDataLandscape* TESRegionDataManager::AsRegionDataLandscape(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 5) {
        return reinterpret_cast<TESRegionDataLandscape*>(a_data);
    }
    return nullptr;
}

TESRegionDataGrass* TESRegionDataManager::AsRegionDataGrass(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 6) {
        return reinterpret_cast<TESRegionDataGrass*>(a_data);
    }
    return nullptr;
}

TESRegionDataSound* TESRegionDataManager::AsRegionDataSound(TESRegionData* a_data) const
{
    if (a_data != nullptr && a_data->GetRegionType() == 7) {
        return reinterpret_cast<TESRegionDataSound*>(a_data);
    }
    return nullptr;
}
