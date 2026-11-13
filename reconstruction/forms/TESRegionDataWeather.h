// TESRegionDataWeather declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s14-tesregiondata-tesregiondataweather
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESRegionData.h for TESRegionData.
// TESRegionDataWeather: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESRegionDataWeather::IsLoaded: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// field10, field18: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/TESRegionData.h"

class TESRegionDataWeather : public TESRegionData
{
public:
    virtual bool IsLoaded() const;  // compared: 0x253ea0

    void* field10;  // 10
    void* field18;  // 18
};
static_assert(sizeof(TESRegionDataWeather) == 0x20, "TESRegionDataWeather size");
