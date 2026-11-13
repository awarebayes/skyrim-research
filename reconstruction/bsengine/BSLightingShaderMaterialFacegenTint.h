// BSLightingShaderMaterialFacegenTint declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialfacegentint
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterial.h for BSLightingShaderMaterial,
// whose constructor and CopyMembers are out-of-line calls in the compared code (0x15235f0, 0x15237e0).
// BSLightingShaderMaterialFacegenTint: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialFacegenTint::GetFeature, BSLightingShaderMaterialFacegenTint::Ctor, BSLightingShaderMaterialFacegenTint::CopyMembers, BSLightingShaderMaterialFacegenTint::~BSLightingShaderMaterialFacegenTint: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSShaderPair: GUESS(low); two adjacent tint components copied together
// fieldA0, fieldA8, unknownAC: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterial.h"

struct BSShaderPair
{
    float first;   // 00
    float second;  // 04
};

class BSLightingShaderMaterialFacegenTint : public BSLightingShaderMaterial
{
public:
    BSLightingShaderMaterialFacegenTint();
    virtual Feature GetFeature() const;  // compared: 0x1526fc0
    BSLightingShaderMaterialFacegenTint* Ctor();  // compared: 0x1526e30
    virtual void CopyMembers(BSShaderMaterial* a_other);  // compared: 0x1526f20
    virtual ~BSLightingShaderMaterialFacegenTint() {}  // compared: 0x1528ec0 (scalar deleting destructor)

    BSShaderPair fieldA0;  // A0
    std::uint32_t fieldA8;  // A8
    std::uint8_t unknownAC[0x4];  // AC
};
static_assert(sizeof(BSLightingShaderMaterialFacegenTint) == 0xB0, "BSLightingShaderMaterialFacegenTint size");
