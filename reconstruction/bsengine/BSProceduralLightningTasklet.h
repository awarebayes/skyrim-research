// BSProceduralLightningTasklet declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s16-bstaskletdata-bsprocedurallightningtasklet
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSTaskletData.h for BSTaskletData.
// BSProceduralLightningTasklet: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSWin32TaskletData: STANDIN EXE_RTTI
// BSProceduralLightningTasklet::OnComplete: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown10, unknown28: GUESS(low)
// field_ac, unknownAD: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSTaskletData.h"

class BSWin32TaskletData : public BSTaskletData
{
public:
    std::uint8_t unknown10[0x18];  // 10
};
static_assert(sizeof(BSWin32TaskletData) == 0x28, "BSWin32TaskletData size");

class BSProceduralLightningTasklet : public BSWin32TaskletData
{
public:
    virtual void OnComplete();  // compared: 0xffe8e0

    std::uint8_t unknown28[0x84];  // 28
    bool field_ac;  // AC
    std::uint8_t unknownAD[0x3];  // AD
};
static_assert(sizeof(BSProceduralLightningTasklet) == 0xB0, "BSProceduralLightningTasklet size");
