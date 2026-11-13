// BSLightingShaderMaterialLandscape declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermateriallandscape
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterialBase.h for
// BSLightingShaderMaterialBase.
// BSLightingShaderMaterialLandscape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialLandscape::GetFeature, BSLightingShaderMaterialLandscape::~BSLightingShaderMaterialLandscape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknownA0: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterialBase.h"

class BSLightingShaderMaterialLandscape : public BSLightingShaderMaterialBase
{
public:
    BSLightingShaderMaterialLandscape();
    virtual Feature GetFeature() const;  // compared: 0x1527a80
    virtual ~BSLightingShaderMaterialLandscape();  // compared: 0x1529030 (scalar deleting destructor)

    std::uint8_t unknownA0[0xB8];  // A0
};
static_assert(sizeof(BSLightingShaderMaterialLandscape) == 0x158, "BSLightingShaderMaterialLandscape size");
