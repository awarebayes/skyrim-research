// BSTempEffectParticle functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bstempeffectparticle
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by gpt-5.6-luna-medium-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x4b04f0, 6 bytes: BSTempEffectParticle::GetType
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSTempEffectParticle.h"

// TODO body: RVA 0x4b04f0, 6 bytes, BSTempEffectParticle::GetType.
TEMP_EFFECT_TYPE BSTempEffectParticle::GetType() const
{
    return static_cast<TEMP_EFFECT_TYPE>(4);
}
