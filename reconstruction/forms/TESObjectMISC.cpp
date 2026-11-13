// TESObjectMISC functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-tesobjectmisc
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x286eb0, 46 bytes: TESObjectMISC::SaveGame
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectMISC.h"

void TESObjectMISC::SaveGame(BGSSaveFormBuffer* a_buf)
{
    TESForm::SaveGame(a_buf);
    saveBlock88.SaveData(a_buf);
}
