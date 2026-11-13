// BSTempEffectParticle declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bstempeffectparticle
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSTempEffect.h for BSTempEffect.
// BSTempEffectParticle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSTempEffectParticle::GetType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSTempEffect.h"

class BSTempEffectParticle : public BSTempEffect
{
public:
    virtual TEMP_EFFECT_TYPE GetType() const;  // compared: 0x4b04f0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown30[0xC0];  // 30
};
static_assert(sizeof(BSTempEffectParticle) == 0xF0, "BSTempEffectParticle size");
