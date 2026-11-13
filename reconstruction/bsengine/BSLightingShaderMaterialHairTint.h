// BSLightingShaderMaterialHairTint declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialhairtint
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterial.h for BSLightingShaderMaterial,
// whose constructor is an out-of-line call in the compared Ctor (0x15235f0).
// BSLightingShaderMaterialHairTint: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialHairTint::~BSLightingShaderMaterialHairTint, BSLightingShaderMaterialHairTint::Ctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// g_hairTintDefaultA, g_hairTintDefaultB: GUESS(low)
// fieldA0, fieldA8, unknownAC: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterial.h"

extern double g_hairTintDefaultA;
extern std::uint32_t g_hairTintDefaultB;

class BSLightingShaderMaterialHairTint : public BSLightingShaderMaterial
{
public:
    BSLightingShaderMaterialHairTint();
    virtual ~BSLightingShaderMaterialHairTint();  // compared: 0x1528fb0 (scalar deleting destructor)
    BSLightingShaderMaterialHairTint* Ctor();  // compared: 0x1527050

    double fieldA0;  // A0
    std::uint32_t fieldA8;  // A8
    std::uint8_t unknownAC[0x4];  // AC
};
static_assert(sizeof(BSLightingShaderMaterialHairTint) == 0xB0, "BSLightingShaderMaterialHairTint size");
