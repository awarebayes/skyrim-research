// AlchemyItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-alchemyitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1466e0, 3 bytes: AlchemyItem::GetDelivery
//   RVA 0x146670, 6 bytes: AlchemyItem::GetCastingType
//   RVA 0x1466d0, 6 bytes: AlchemyItem::GetDataSize
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "AlchemyItem.h"

// RVA 0x1466e0, 3 bytes: returns delivery 0.
MagicSystem::Delivery AlchemyItem::GetDelivery() const
{
    return static_cast<MagicSystem::Delivery>(0);
}

// RVA 0x146670, 6 bytes: returns casting type 1.
MagicSystem::CastingType AlchemyItem::GetCastingType() const
{
    return static_cast<MagicSystem::CastingType>(1);
}

// RVA 0x1466d0, 6 bytes: returns 0x20.
std::uint32_t AlchemyItem::GetDataSize() const
{
    return 0x20;
}
