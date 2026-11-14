// MagicTarget functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magictarget
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x17ee10, 3 bytes: MagicTarget::GetTargetStatsObject
//   RVA 0x17ee30, 3 bytes: MagicTarget::IsInvulnerable
//   RVA 0x17eea0, 3 bytes: MagicTarget::MagicTargetIsActor
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "MagicTarget.h"

TESObjectREFR* MagicTarget::GetTargetStatsObject()
{
    return nullptr;
}

bool MagicTarget::IsInvulnerable()
{
    return false;
}

bool MagicTarget::MagicTargetIsActor() const
{
    return false;
}
