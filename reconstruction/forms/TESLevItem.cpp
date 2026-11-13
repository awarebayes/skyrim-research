// TESLevItem functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-teslevitem
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x272170, 43 bytes: TESLevItem::LoadGame
// Adapted bodies: TESLevItem::LoadGame ~ momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/teslevcharacter.cpp:19 (no-licence) (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESLevItem.h"

// TODO body: RVA 0x272170, 43 bytes, TESLevItem::LoadGame.
void TESLevItem::LoadGame(BGSLoadFormBuffer* a_buf)
{
    TESForm::LoadGame(a_buf);
    return leveledList.LoadGame(a_buf);
}
