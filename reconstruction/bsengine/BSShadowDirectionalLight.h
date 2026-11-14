// BSShadowDirectionalLight declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsshadowdirectionallight
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiRefObject.h for NiRefObject.
// BSShadowDirectionalLight: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSLight, BSShadowLight: STANDIN EXE_RTTI
// BSShadowDirectionalLight::GetPassExtraParam: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown10, unknown140, unknown560: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiRefObject.h"

class BSLight : public NiRefObject
{
public:
    std::uint8_t unknown10[0x130];  // 10
};
static_assert(sizeof(BSLight) == 0x140, "BSLight size");

class BSShadowLight : public BSLight
{
public:
    std::uint8_t unknown140[0x420];  // 140
};
static_assert(sizeof(BSShadowLight) == 0x560, "BSShadowLight size");

class BSShadowDirectionalLight : public BSShadowLight
{
public:
    virtual std::uint32_t GetPassExtraParam(std::uint32_t a_accumFlag);  // compared: 0x157ed10
    // GetIsFrustumOrDirectionalLight, GetIsDirectionalLight, GetNeedsClipPlanes: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); each returns true
    virtual bool GetIsFrustumOrDirectionalLight();
    virtual bool GetIsDirectionalLight();
    virtual bool GetNeedsClipPlanes();

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown560[0x58];  // 560
};
static_assert(sizeof(BSShadowDirectionalLight) == 0x5B8, "BSShadowDirectionalLight size");
