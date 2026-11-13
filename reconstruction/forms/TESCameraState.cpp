// TESCameraState functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s26-bsintrusiverefcounted-tescamerastate
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x24a020, 11 bytes: TESCameraState::GetRotation
//   RVA 0x24a030, 39 bytes: TESCameraState::GetTranslation
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESCameraState.h"

void TESCameraState::GetRotation(NiQuaternion& a_rotation)
{
    a_rotation = niQuatDefault;
}

void TESCameraState::GetTranslation(NiPoint3& a_translation)
{
    a_translation.x = niPointZero.x;
    a_translation.y = niPointZero.y;
    a_translation.z = niPointZero.z;
}
