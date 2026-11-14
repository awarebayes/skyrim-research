// BSISoundCategory functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsisoundcategory
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x329dc0, 43 bytes: BSISoundCategory::~BSISoundCategory
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSISoundCategory.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSISoundCategory::BSISoundCategory()
{
}

// RVA 0x329dc0, 43 bytes: the target inlines the complete destructor, so the body is empty.
BSISoundCategory::~BSISoundCategory()
{
}
