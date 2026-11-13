// BSLightingShaderMaterialParallaxOcc declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialparallaxocc
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterial.h for
// BSLightingShaderMaterial.
// BSLightingShaderMaterialParallaxOcc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialParallaxOcc::Ctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknownA0: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterial.h"

class BSLightingShaderMaterialParallaxOcc : public BSLightingShaderMaterial
{
public:
    BSLightingShaderMaterialParallaxOcc();
    BSLightingShaderMaterialParallaxOcc* Ctor();  // compared: 0x1526170

    // unknownA0: GUESS(low)
    std::uint64_t unknownA0;  // A0
    // unknownA8: GUESS(low)
    std::uint64_t unknownA8;  // A8
};
static_assert(sizeof(BSLightingShaderMaterialParallaxOcc) == 0xB0, "BSLightingShaderMaterialParallaxOcc size");
