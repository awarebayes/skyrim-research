// NiFloatInterpolator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-nifloatinterpolator
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/o2-fpfast.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf617d0, 14 bytes: NiFloatInterpolator::GetKeyCount
//   RVA 0xf617f0, 14 bytes: NiFloatInterpolator::GetKeyContent
//   RVA 0xf61980, 14 bytes: NiFloatInterpolator::GuaranteeTimeRange
//   RVA 0xf61820, 15 bytes: NiFloatInterpolator::GetKeyArray
//   RVA 0xf61840, 15 bytes: NiFloatInterpolator::GetKeyStride
//   RVA 0xf61860, 27 bytes: NiFloatInterpolator::GetChannelPosed
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiFloatInterpolator.h"

std::uint32_t NiFloatInterpolator::GetKeyCount(std::uint16_t a_channel) const
{
    if (unk20 == nullptr) {
        return 0;
    }
    return unk20->keyCount;
}

KeyContent NiFloatInterpolator::GetKeyContent(std::uint16_t a_channel) const
{
    if (unk20 == nullptr) {
        return static_cast<KeyContent>(0);
    }
    return unk20->keyContent;
}

void NiFloatInterpolator::GuaranteeTimeRange(float a_start, float a_end)
{
    if (unk20 == nullptr) {
        return;
    }
    GuaranteeFloatTimeRange(unk20, a_start, a_end);
}

void* NiFloatInterpolator::GetKeyArray(std::uint16_t a_channel) const
{
    if (unk20 == nullptr) {
        return nullptr;
    }
    return unk20->keyArray;
}

std::uint8_t NiFloatInterpolator::GetKeyStride(std::uint16_t a_channel) const
{
    if (unk20 == nullptr) {
        return 0;
    }
    return unk20->keyStride;
}

bool NiFloatInterpolator::GetChannelPosed(std::uint16_t a_channel) const
{
    return unk20 == nullptr && -3.4028234663852886e+38f != unk18;
}
