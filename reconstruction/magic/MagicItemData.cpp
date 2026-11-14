// MagicItemData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemdata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-4 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x956d90, 6 bytes: MagicItemData::GetCount
//   RVA 0x951e80, 9 bytes: MagicItemData::GetEnabled
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "MagicItemData.h"

// ReadEnabledFlag: GUESS(low)
bool ReadEnabledFlag(void* a_data);

// RVA 0x956d90, 6 bytes, MagicItemData::GetCount.
std::uint32_t MagicItemData::GetCount()
{
    return 1;
}

// RVA 0x951e80, 9 bytes, MagicItemData::GetEnabled.
bool MagicItemData::GetEnabled()
{
    return ReadEnabledFlag(data18);
}
