// BSLightingShaderMaterial declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterial
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterialBase.h for
// BSLightingShaderMaterialBase.
// BSLightingShaderMaterial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterial::~BSLightingShaderMaterial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterialBase.h"

class BSLightingShaderMaterial : public BSLightingShaderMaterialBase
{
public:
    BSLightingShaderMaterial();
    virtual ~BSLightingShaderMaterial();  // compared: 0x4b4a00 (scalar deleting destructor)
};
static_assert(sizeof(BSLightingShaderMaterial) == 0xA0, "BSLightingShaderMaterial size");
