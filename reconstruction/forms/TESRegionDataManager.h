// TESRegionDataManager declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s36-tesregiondatamanager-tesregiondatamanager
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// TESRegionDataManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESRegionDataManager::AsRegionDataObjects, TESRegionDataManager::AsRegionDataWeather, TESRegionDataManager::AsRegionDataMap, TESRegionDataManager::AsRegionDataLandscape, TESRegionDataManager::AsRegionDataGrass, TESRegionDataManager::AsRegionDataSound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESRegionDataObjects, TESRegionDataWeather, TESRegionDataMap, TESRegionDataLandscape, TESRegionDataGrass, TESRegionDataSound: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESRegionData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESRegionData::unk01, TESRegionData::unk02, TESRegionData::GetRegionType: GUESS(low)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class TESRegionDataObjects;
class TESRegionDataWeather;
class TESRegionDataMap;
class TESRegionDataLandscape;
class TESRegionDataGrass;
class TESRegionDataSound;

class TESRegionData
{
public:
    virtual ~TESRegionData();  // 00
    virtual void unk01();  // 01
    virtual void unk02();  // 02
    virtual std::int32_t GetRegionType() const;  // 03
};

class TESRegionDataManager
{
public:
    virtual TESRegionDataObjects* AsRegionDataObjects(TESRegionData* a_data) const;  // compared: 0x251870
    virtual TESRegionDataWeather* AsRegionDataWeather(TESRegionData* a_data) const;  // compared: 0x2518b0
    virtual TESRegionDataMap* AsRegionDataMap(TESRegionData* a_data) const;  // compared: 0x2518f0
    virtual TESRegionDataLandscape* AsRegionDataLandscape(TESRegionData* a_data) const;  // compared: 0x251930
    virtual TESRegionDataGrass* AsRegionDataGrass(TESRegionData* a_data) const;  // compared: 0x251970
    virtual TESRegionDataSound* AsRegionDataSound(TESRegionData* a_data) const;  // compared: 0x2519b0

    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(TESRegionDataManager) == 0x10, "TESRegionDataManager size");
