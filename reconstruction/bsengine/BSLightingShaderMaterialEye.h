// BSLightingShaderMaterialEye declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bslightingshadermaterialeye
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterialBase.h for
// BSLightingShaderMaterialBase.
// BSLightingShaderMaterialEye: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialEye::SaveBinary, BSLightingShaderMaterialEye::LoadBinary, BSLightingShaderMaterialEye::ReceiveValuesFromRootMaterial, BSLightingShaderMaterialEye::Ctor, BSLightingShaderMaterialEye::ComputeCRC32: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// eyeEnvMask, eyeCubemap, unkB0, colorB4, colorC0, pad_CC: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../bsengine/BSLightingShaderMaterialBase.h"

class BSLightingShaderMaterialEye : public BSLightingShaderMaterialBase
{
public:
    Feature GetFeature() const override;
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0x1525770
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0x15257f0
    virtual void ReceiveValuesFromRootMaterial(bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN);  // compared: 0x1525640
    BSLightingShaderMaterialEye* Ctor();  // compared: 0x15250e0
    virtual std::uint32_t ComputeCRC32();  // compared: 0x15253e0

    NiPointer<NiSourceTexture> eyeEnvMask;  // A0
    NiPointer<NiSourceTexture> eyeCubemap;  // A8
    float                      unkB0;       // B0
    NiColor                    colorB4;     // B4
    NiColor                    colorC0;     // C0
    std::uint32_t              pad_CC;      // CC
};
static_assert(sizeof(BSLightingShaderMaterialEye) == 0xD0, "BSLightingShaderMaterialEye size");
