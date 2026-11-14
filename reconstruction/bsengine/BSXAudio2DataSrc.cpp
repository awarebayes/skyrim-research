// BSXAudio2DataSrc functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsxaudio2datasrc
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xcdc8e0, 52 bytes: BSXAudio2DataSrc::~BSXAudio2DataSrc (declared in the header, not
//   defined here: the target calls the complete destructor, so attempt binds that call)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSXAudio2DataSrc.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSXAudio2DataSrc::BSXAudio2DataSrc()
{
}

