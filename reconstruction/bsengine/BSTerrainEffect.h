// BSTerrainEffect declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsterraineffect
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSTempEffect.h for BSTempEffect.
// BSTerrainEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSTerrainEffect::GetManagerHandlesSaveLoad: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown30: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSTempEffect.h"

class BSTerrainEffect : public BSTempEffect
{
public:
    virtual bool GetManagerHandlesSaveLoad() const;  // compared: 0x4b7c40

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown30[0x88];  // 30
};
static_assert(sizeof(BSTerrainEffect) == 0xB8, "BSTerrainEffect size");
