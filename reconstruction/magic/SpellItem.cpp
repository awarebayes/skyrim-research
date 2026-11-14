// SpellItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-spellitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x154d10, 6 bytes: SpellItem::GetDataSize
//   RVA 0x155cf0, 7 bytes: SpellItem::GetCastingType
//   RVA 0x155d00, 7 bytes: SpellItem::GetSpellType
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "SpellItem.h"

std::uint32_t SpellItem::GetDataSize() const
{
    return 0x28;
}

MagicSystem::CastingType SpellItem::GetCastingType() const
{
    return static_cast<MagicSystem::CastingType>(castingType);
}

MagicSystem::SpellType SpellItem::GetSpellType() const
{
    return static_cast<MagicSystem::SpellType>(spellType);
}
