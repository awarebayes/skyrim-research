// BSLightingShaderMaterialLODLandscape declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermateriallodlandscape
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterialBase.h for
// BSLightingShaderMaterialBase.
// BSLightingShaderMaterialLODLandscape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialLODLandscape::GetFeature: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknownA0: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSLightingShaderMaterialBase.h"

class BSLightingShaderMaterialLODLandscape : public BSLightingShaderMaterialBase
{
public:
    virtual Feature GetFeature() const;  // compared: 0x1527fb0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknownA0[0x28];  // A0
};
static_assert(sizeof(BSLightingShaderMaterialLODLandscape) == 0xC8, "BSLightingShaderMaterialLODLandscape size");
