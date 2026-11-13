// TESLevCharacter functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-teslevcharacter
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x2717b0, 64 bytes: TESLevCharacter::InitItemImpl
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESLevCharacter.h"

// Body done: RVA 0x2717b0, 64 bytes, TESLevCharacter::InitItemImpl. The flag test guards the
// whole initialisation; the last call is a tail call in the target.
void TESLevCharacter::InitItemImpl()
{
    if (!TestBit(formFlags, 3)) {
        InitLeveledListState(unknown30, this);
        InitModelTextureSwapState(unknown58, this);
        ResetOwnerState(this, true);
    }
}
