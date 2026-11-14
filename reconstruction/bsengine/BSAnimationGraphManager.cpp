// BSAnimationGraphManager functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsanimationgraphmanager
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xbc3c30, 52 bytes: BSAnimationGraphManager::~BSAnimationGraphManager
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSAnimationGraphManager.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSAnimationGraphManager::BSAnimationGraphManager()
{
}

// RVA 0xbc3c30, 52 bytes: the destructor is declared in the header only. The target calls the
// complete base destructor first, then tests bit 0 of the flag argument before freeing the object.
