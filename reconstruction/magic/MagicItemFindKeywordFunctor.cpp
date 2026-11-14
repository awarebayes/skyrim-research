// MagicItemFindKeywordFunctor functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemfindkeywordfunctor
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x152790, 43 bytes: MagicItemFindKeywordFunctor::~MagicItemFindKeywordFunctor
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "MagicItemFindKeywordFunctor.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
MagicItemFindKeywordFunctor::MagicItemFindKeywordFunctor()
{
}

// RVA 0x152790, 43 bytes, MagicItemFindKeywordFunctor::~MagicItemFindKeywordFunctor; compared as the
// scalar deleting destructor. The target stores the vftable and frees the object itself, so the
// complete destructor is empty.
MagicItemFindKeywordFunctor::~MagicItemFindKeywordFunctor()
{
}
