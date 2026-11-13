// NiFloatInterpolator declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-nifloatinterpolator
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiKeyBasedInterpolator.h for NiKeyBasedInterpolator.
// NiFloatInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiFloatInterpolator::GetKeyCount, NiFloatInterpolator::GetKeyContent, NiFloatInterpolator::GuaranteeTimeRange, NiFloatInterpolator::GetKeyArray, NiFloatInterpolator::GetKeyStride, NiFloatInterpolator::GetChannelPosed: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown28, unk18, unk20: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiKeyBasedInterpolator.h"

// KeyContent: GUESS(low); a 4-byte enum, so GetKeyContent returns it in EAX
enum class KeyContent : std::uint32_t {};

// NiFloatData: GUESS(low); the key data behind NiFloatInterpolator's pointer at 0x20, layout from the listings
class NiFloatData
{
public:
    std::uint8_t  unknown00[0x10];  // 00
    std::uint32_t keyCount;         // 10
    std::uint8_t  unknown14[0x4];   // 14
    void*         keyArray;         // 18
    KeyContent    keyContent;       // 20
    std::uint8_t  keyStride;        // 24
};

// GuaranteeFloatTimeRange: GUESS(low); the callee at RVA 0xf60df0, bound by the unit's bind-hints.json
void GuaranteeFloatTimeRange(void* a_data, float a_start, float a_end);

class NiFloatInterpolator : public NiKeyBasedInterpolator
{
public:
    virtual std::uint32_t GetKeyCount(std::uint16_t a_channel) const;  // compared: 0xf617d0
    virtual KeyContent GetKeyContent(std::uint16_t a_channel) const;  // compared: 0xf617f0
    virtual void GuaranteeTimeRange(float a_start, float a_end);  // compared: 0xf61980
    virtual void* GetKeyArray(std::uint16_t a_channel) const;  // compared: 0xf61820
    virtual std::uint8_t GetKeyStride(std::uint16_t a_channel) const;  // compared: 0xf61840
    virtual bool GetChannelPosed(std::uint16_t a_channel) const;  // compared: 0xf61860

    float        unk18;        // 18
    NiFloatData* unk20;        // 20
    std::uint8_t unknown28[0x8];  // 28
};
static_assert(sizeof(NiFloatInterpolator) == 0x30, "NiFloatInterpolator size");
