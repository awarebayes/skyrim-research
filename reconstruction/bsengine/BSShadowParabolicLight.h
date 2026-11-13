// BSShadowParabolicLight declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsshadowparaboliclight
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiRefObject.h for NiRefObject.
// BSShadowParabolicLight: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSLight, BSShadowLight: STANDIN EXE_RTTI
// BSShadowParabolicLight::GetIsOmniLight, BSShadowParabolicLight::ReturnShadowmaps: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown10, unknown140: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiRefObject.h"

class BSLight : public NiRefObject
{
public:
    std::uint8_t unknown10[0x130];  // 10
};
static_assert(sizeof(BSLight) == 0x140, "BSLight size");

struct ShadowmapTarget
{
    std::uint8_t unknown00[0x144];  // 00
    std::uint32_t state144;  // 144
};

class BSShadowLight : public BSLight
{
public:
    // state140: GUESS(low)
    std::uint32_t state140;  // 140
    std::uint8_t unknown144[0x4];  // 144
    // shadowmap148: GUESS(low)
    ShadowmapTarget* shadowmap148;  // 148
    std::uint8_t unknown150[0x410];  // 150
};
static_assert(sizeof(BSShadowLight) == 0x560, "BSShadowLight size");

class BSShadowParabolicLight : public BSShadowLight
{
public:
    virtual bool GetIsOmniLight();  // compared: 0x1588e20
    virtual void ReturnShadowmaps();  // compared: 0x1588d50
    // ReturnShadowmapsTarget: GUESS(low)
    void ReturnShadowmapsTarget();
};
static_assert(sizeof(BSShadowParabolicLight) == 0x560, "BSShadowParabolicLight size");
