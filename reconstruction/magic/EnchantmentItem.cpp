// EnchantmentItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-enchantmentitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x14e760, 6 bytes: EnchantmentItem::GetChunkID
//   RVA 0x14e790, 6 bytes: EnchantmentItem::GetDataSize
//   RVA 0x14e780, 8 bytes: EnchantmentItem::GetData1
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "EnchantmentItem.h"

// RVA 0x14e760, 6 bytes: returns the chunk tag 'ENIT'.
std::uint32_t EnchantmentItem::GetChunkID()
{
    return 0x54494E45;
}

// RVA 0x14e790, 6 bytes: returns 0x30.
std::uint32_t EnchantmentItem::GetDataSize() const
{
    return 0x30;
}

// RVA 0x14e780, 8 bytes: the data block starts at +0x90.
const MagicItem::Data* EnchantmentItem::GetData1() const
{
    return reinterpret_cast<const MagicItem::Data*>(unknown90);
}
