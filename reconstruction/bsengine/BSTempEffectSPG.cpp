// BSTempEffectSPG functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bstempeffectspg
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x4b5800, 6 bytes: BSTempEffectSPG::GetType
//   RVA 0x4b5250, 53 bytes: BSTempEffectSPG::FinishLoadGame
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSTempEffectSPG.h"

// The value 6 is not a named enumerator in the shared TEMP_EFFECT_TYPE; the target returns it as a literal.
TEMP_EFFECT_TYPE BSTempEffectSPG::GetType() const
{
    return static_cast<TEMP_EFFECT_TYPE>(6);
}
