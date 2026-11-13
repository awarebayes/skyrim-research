// BSLightingShaderMaterialFacegen declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialfacegen
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterial.h for BSLightingShaderMaterial,
// whose constructor is an out-of-line call in the compared Ctor (0x15235f0).
// BSLightingShaderMaterialFacegen: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialFacegen::~BSLightingShaderMaterialFacegen, BSLightingShaderMaterialFacegen::Ctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// fieldA0, fieldA8, fieldB0: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterial.h"

class BSLightingShaderMaterialFacegen : public BSLightingShaderMaterial
{
public:
    BSLightingShaderMaterialFacegen();
    virtual ~BSLightingShaderMaterialFacegen();  // compared: 0x1528e80 (scalar deleting destructor)
    BSLightingShaderMaterialFacegen* Ctor();  // compared: 0x1526760

    std::uint64_t fieldA0;  // A0
    std::uint64_t fieldA8;  // A8
    std::uint64_t fieldB0;  // B0
};
static_assert(sizeof(BSLightingShaderMaterialFacegen) == 0xB8, "BSLightingShaderMaterialFacegen size");
