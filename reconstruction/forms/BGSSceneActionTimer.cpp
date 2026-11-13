// BGSSceneActionTimer functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneactiontimer
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3ad170, 18 bytes: BGSSceneActionTimer::Unk_0D
//   RVA 0x3ad400, 43 bytes: BGSSceneActionTimer::~BGSSceneActionTimer
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSSceneActionTimer.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSSceneActionTimer::BGSSceneActionTimer()
{
}

// TODO body: RVA 0x3ad400, 43 bytes, BGSSceneActionTimer::~BGSSceneActionTimer; compared as the
// scalar deleting destructor. If the target calls a separate destructor, keep only the declaration
// and delete this definition (cookbook rule 18).
BGSSceneActionTimer::~BGSSceneActionTimer() {}
