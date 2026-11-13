// BSShaderAccumulator declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsshaderaccumulator
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObject.h for NiObject.
// BSShaderAccumulator: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// NiAccumulator, NiBackToFrontAccumulator, NiAlphaAccumulator: STANDIN EXE_RTTI
// BSShaderAccumulator::GetCurrentAccumulator, BSShaderAccumulator::SetCurrentAccumulator, BSShaderAccumulator::StartGroupingAlphas, BSShaderAccumulator::FinishAccumulatingPostResolveDepth: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// NiAccumulator::FinishAccumulating: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); virtual no-argument base method; the qualified call targets the base implementation
// NiBound: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// BSBatchRenderer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSBatchRenderer::GeometryGroup: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); declared here only as a forward class
// PrepareDepth, BuildAlphaGroups: GUESS(low); the two helpers the listings call
// unknown10, unknown18, unknown51, unknown130, unknown150: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObject.h"

class NiBound;

// Only the nested type is needed here; the rest of the community BSBatchRenderer is not modelled.
class BSBatchRenderer
{
public:
    class GeometryGroup;
};

class NiAccumulator : public NiObject
{
public:
    virtual void FinishAccumulating();  // base implementation, 0xf1ede0

    // The compared code reads this qword at 0x10 (as a call argument).
    std::uint64_t unknown10;  // 10
};
static_assert(sizeof(NiAccumulator) == 0x18, "NiAccumulator size");

class NiBackToFrontAccumulator : public NiAccumulator
{
public:
};

class NiAlphaAccumulator : public NiBackToFrontAccumulator
{
public:
    std::uint8_t unknown18[0x39];  // 18
    std::uint8_t unknown51;        // 51, byte read as a call argument
    std::uint8_t unknown52[0x6];   // 52
};
static_assert(sizeof(NiAlphaAccumulator) == 0x58, "NiAlphaAccumulator size");

class BSShaderAccumulator : public NiAlphaAccumulator
{
public:
    static BSShaderAccumulator* GetCurrentAccumulator();  // compared: 0x14ecb90
    static void SetCurrentAccumulator(BSShaderAccumulator* a_accumulator);  // compared: 0x14ecba0
    virtual BSBatchRenderer::GeometryGroup* StartGroupingAlphas(NiBound* a_bound);  // compared: 0x1520d50
    virtual void FinishAccumulatingPostResolveDepth(std::uint32_t flags);  // compared: 0x151ef00

    void PrepareDepth();

    // Members used by the compared bodies, split out of the padding; offsets are checked by the size assert.
    std::uint8_t unknown58[0xD8];  // 58
    std::uint64_t unknown130;      // 130
    std::uint8_t unknown138[0x18];  // 138
    std::uint32_t unknown150;      // 150
    std::uint8_t unknown154[0x2C];  // 154
};
static_assert(sizeof(BSShaderAccumulator) == 0x180, "BSShaderAccumulator size");
