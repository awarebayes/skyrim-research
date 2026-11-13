// BSTempEffectSPG declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bstempeffectspg
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSTempEffect.h for BSTempEffect.
// BSTempEffectSPG: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSTempEffectSPG::GetType, BSTempEffectSPG::FinishLoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSTempEffect.h"

class BSTempEffectSPG : public BSTempEffect
{
public:
    virtual TEMP_EFFECT_TYPE GetType() const;  // compared: 0x4b5800
    virtual void FinishLoadGame(BGSLoadGameBuffer* a_buf);  // compared: 0x4b5250

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown30[0x20];  // 30
};
static_assert(sizeof(BSTempEffectSPG) == 0x50, "BSTempEffectSPG size");
