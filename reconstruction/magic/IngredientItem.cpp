// IngredientItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-ingredientitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x14fd30, 3 bytes: IngredientItem::GetDelivery
//   RVA 0x14fce0, 6 bytes: IngredientItem::GetCastingType
//   RVA 0x14fcf0, 6 bytes: IngredientItem::GetChunkID
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "IngredientItem.h"

MagicSystem::Delivery IngredientItem::GetDelivery() const
{
    return static_cast<MagicSystem::Delivery>(0);
}

MagicSystem::CastingType IngredientItem::GetCastingType() const
{
    return static_cast<MagicSystem::CastingType>(1);
}

std::uint32_t IngredientItem::GetChunkID()
{
    return 0x54494E45;
}
