// BSBloodSplatterShaderProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsbloodsplattershaderproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSShaderProperty.h for BSShaderProperty.
// BSBloodSplatterShaderProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSBloodSplatterShaderProperty::QShader, BSBloodSplatterShaderProperty::GetBaseTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk88: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSShaderProperty.h"

class BSBloodSplatterShaderProperty : public BSShaderProperty
{
public:
    virtual std::int32_t QShader();  // compared: 0x152d8a0
    virtual NiSourceTexture* GetBaseTexture();  // compared: 0x152db70

    NiSourceTexture* unk88;  // 88
    std::uint8_t     unk90[0x20];  // 90
};
static_assert(sizeof(BSBloodSplatterShaderProperty) == 0xB0, "BSBloodSplatterShaderProperty size");
