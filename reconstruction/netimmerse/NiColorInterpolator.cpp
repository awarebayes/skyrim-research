// NiColorInterpolator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nicolorinterpolator
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by gpt-5.6-luna-medium-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf62970, 6 bytes: NiColorInterpolator::GetKeyType
//   RVA 0xf62d80, 8 bytes: NiColorInterpolator::GetRTTI
//   RVA 0xf62930, 14 bytes: NiColorInterpolator::GetKeyCount
//   RVA 0xf62950, 14 bytes: NiColorInterpolator::GetKeyContent
//   RVA 0xf62b50, 14 bytes: NiColorInterpolator::GuaranteeTimeRange
//   RVA 0xf62980, 15 bytes: NiColorInterpolator::GetKeyArray
//   RVA 0xf629a0, 15 bytes: NiColorInterpolator::GetKeyStride
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiColorInterpolator.h"

const NiRTTI NiRTTI_NiColorInterpolator{};
void GuaranteeTimeRangeImpl(NiColorKeyData*, float, float);

// TODO body: RVA 0xf62970, 6 bytes, NiColorInterpolator::GetKeyType.
KeyType NiColorInterpolator::GetKeyType(std::uint16_t a_channel) const
{
    return static_cast<KeyType>(3);
}

// TODO body: RVA 0xf62d80, 8 bytes, NiColorInterpolator::GetRTTI.
const NiRTTI* NiColorInterpolator::GetRTTI() const
{
    return &NiRTTI_NiColorInterpolator;
}

// TODO body: RVA 0xf62930, 14 bytes, NiColorInterpolator::GetKeyCount.
std::uint32_t NiColorInterpolator::GetKeyCount(std::uint16_t a_channel) const
{
    if (!keyData) {
        return 0;
    }
    return keyData->keyCount;
}

// TODO body: RVA 0xf62950, 14 bytes, NiColorInterpolator::GetKeyContent.
KeyContent NiColorInterpolator::GetKeyContent(std::uint16_t a_channel) const
{
    if (!keyData) {
        return static_cast<KeyContent>(0);
    }
    return keyData->keyContent;
}

// TODO body: RVA 0xf62b50, 14 bytes, NiColorInterpolator::GuaranteeTimeRange.
void NiColorInterpolator::GuaranteeTimeRange(float a_start, float a_end)
{
    if (keyData) {
        return GuaranteeTimeRangeImpl(keyData, a_start, a_end);
    }
}

// TODO body: RVA 0xf62980, 15 bytes, NiColorInterpolator::GetKeyArray.
void* NiColorInterpolator::GetKeyArray(std::uint16_t a_channel) const
{
    if (!keyData) {
        return nullptr;
    }
    return keyData->keyArray;
}

// TODO body: RVA 0xf629a0, 15 bytes, NiColorInterpolator::GetKeyStride.
std::uint8_t NiColorInterpolator::GetKeyStride(std::uint16_t a_channel) const
{
    if (!keyData) {
        return 0;
    }
    return keyData->keyStride;
}
