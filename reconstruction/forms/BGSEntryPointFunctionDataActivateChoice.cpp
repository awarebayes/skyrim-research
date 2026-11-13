// BGSEntryPointFunctionDataActivateChoice functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s07-bgsentrypointfunctiondataactivatechoice
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x38ea80, 5 bytes: BGSEntryPointFunctionDataActivateChoice::Unk_05
//   RVA 0x38ea90, 5 bytes: BGSEntryPointFunctionDataActivateChoice::SetPerk
//   RVA 0x38eaa0, 5 bytes: BGSEntryPointFunctionDataActivateChoice::GetPerk
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSEntryPointFunctionDataActivateChoice.h"

std::uint16_t BGSEntryPointFunctionDataActivateChoice::Unk_05()
{
    return field22;
}

void BGSEntryPointFunctionDataActivateChoice::SetPerk(BGSPerk* a_perk)
{
    perk10 = a_perk;
}

BGSPerk* BGSEntryPointFunctionDataActivateChoice::GetPerk()
{
    return perk10;
}
