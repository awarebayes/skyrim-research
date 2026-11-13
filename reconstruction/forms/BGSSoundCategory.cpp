// BGSSoundCategory functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgssoundcategory
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3299e0, 5 bytes: BGSSoundCategory::SetCategoryAttenuation
//   RVA 0x329970, 6 bytes: BGSSoundCategory::SetCategoryFrequency
//   RVA 0x329790, 17 bytes: BGSSoundCategory::InitializeData
//   RVA 0x329820, 64 bytes: BGSSoundCategory::Matches
// Stuck functions, kept in near-miss/: RVA 0x329920 (GetCategoryFrequency) and RVA 0x3298d0
// (SetCategoryVolume).
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSSoundCategory.h"

void BGSSoundCategory::SetCategoryAttenuation(std::uint16_t a_value)
{
    RawAt<std::uint16_t>(this, 0x1a) = a_value;
}

void BGSSoundCategory::SetCategoryFrequency(float a_value)
{
    RawAt<float>(this, 0x24) = a_value;
}

void BGSSoundCategory::InitializeData()
{
    RawAt<std::uint32_t>(this, 0x4c) = 0xffffffff;
    RawAt<std::uint32_t>(this, 0x38) = 0;
    RawAt<std::uint64_t>(this, 0x40) = 0;
}

bool BGSSoundCategory::Matches(const BSISoundCategory* a_category) const
{
    const std::uintptr_t primary = reinterpret_cast<std::uintptr_t>(this) - 0x30;
    const BSISoundCategory* self = primary == 0 ? nullptr : reinterpret_cast<const BSISoundCategory*>(this);
    if (self == a_category) {
        return true;
    }
    BGSSoundCategory* parent = RawAt<BGSSoundCategory*>(this, 0x10);
    if (parent == nullptr) {
        return false;
    }
    const BSISoundCategory* iface = reinterpret_cast<const BSISoundCategory*>(reinterpret_cast<const std::uint8_t*>(parent) + 0x30);
    if (iface->Matches(a_category)) {
        return true;
    }
    return false;
}
