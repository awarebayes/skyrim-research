// MagicItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x146770, 3 bytes: MagicItem::GetMaxEffectCount
//   RVA 0x14e7c0, 3 bytes: MagicItem::IsMedicine
//   RVA 0x14e830, 3 bytes: MagicItem::LoadMagicItemChunk
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "MagicItem.h"

std::uint32_t MagicItem::GetMaxEffectCount() const
{
    return 0;
}

bool MagicItem::IsMedicine() const
{
    return false;
}

void MagicItem::LoadMagicItemChunk(TESFile* a_mod, std::uint32_t a_chunkID)
{
}
