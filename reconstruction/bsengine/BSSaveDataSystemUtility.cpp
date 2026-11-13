// BSSaveDataSystemUtility functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s30-bsteventsource-vbssavedatae-bssavedatasystemutili
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x159af80, 11 bytes: BSSaveDataSystemUtility::Unk_0B
//   RVA 0x159ab30, 34 bytes: BSSaveDataSystemUtility::Unk_0A
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSSaveDataSystemUtility.h"

std::uint64_t* BSSaveDataSystemUtility::Unk_0B(std::uint64_t* a_out)
{
    *a_out = 0;
    return a_out;
}

std::uint32_t BSSaveDataSystemUtility::Unk_0A(void* a_obj)
{
    std::uint32_t value = 0;
    LookupValue(a_obj, &value);
    return value;
}

// RVA 0x159a9e0, 3 bytes: returns true.
bool BSSaveDataSystemUtility::Unk_08()
{
    return true;
}

// RVA 0x159a9f0, 3 bytes: returns true.
bool BSSaveDataSystemUtility::Unk_07()
{
    return true;
}

// RVA 0x159aa00, 3 bytes: an empty slot body.
void BSSaveDataSystemUtility::Unk_05()
{
}
