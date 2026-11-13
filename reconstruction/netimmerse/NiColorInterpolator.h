// NiColorInterpolator declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nicolorinterpolator
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiKeyBasedInterpolator.h for NiKeyBasedInterpolator.
// NiColorInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiColorInterpolator::GetKeyType, NiColorInterpolator::GetRTTI, NiColorInterpolator::GetKeyCount, NiColorInterpolator::GetKeyContent, NiColorInterpolator::GuaranteeTimeRange, NiColorInterpolator::GetKeyArray, NiColorInterpolator::GetKeyStride: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// keyData: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiKeyBasedInterpolator.h"

class NiRTTI
{
public:
    const char* name;
};
enum class KeyType : std::uint32_t {};
enum class KeyContent : std::uint32_t {};

// keyData: GUESS(low); fields correspond to the selected key-data accessors.
struct NiColorKeyData
{
    std::uint8_t unknown00[0x10];
    std::uint32_t keyCount;  // 10
    std::uint8_t unknown14[0x4];  // 14
    void* keyArray;  // 18
    KeyContent keyContent;  // 20
    std::uint8_t keyStride;  // 24
};

// TODO type KeyType: used by value: declare it (an enum or a small class) before the class.
// TODO type KeyContent: used by value: declare it (an enum or a small class) before the class.

class NiColorInterpolator : public NiKeyBasedInterpolator
{
public:
    virtual KeyType GetKeyType(std::uint16_t a_channel) const;  // compared: 0xf62970
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xf62d80
    virtual std::uint32_t GetKeyCount(std::uint16_t a_channel) const;  // compared: 0xf62930
    virtual KeyContent GetKeyContent(std::uint16_t a_channel) const;  // compared: 0xf62950
    virtual void GuaranteeTimeRange(float a_start, float a_end);  // compared: 0xf62b50
    virtual void* GetKeyArray(std::uint16_t a_channel) const;  // compared: 0xf62980
    virtual std::uint8_t GetKeyStride(std::uint16_t a_channel) const;  // compared: 0xf629a0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown18[0x10];  // 18
    NiColorKeyData* keyData;  // 28
    std::uint8_t unknown30[0x8];  // 30
};
static_assert(sizeof(NiColorInterpolator) == 0x38, "NiColorInterpolator size");
