// BSPortalGraphEntry functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsportalgraphentry
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfdb1f0, 52 bytes: BSPortalGraphEntry::~BSPortalGraphEntry (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSPortalGraphEntry.h"

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared. The destructor itself stays undefined here so that the compiler
// calls the separate complete destructor, as the listing does.
BSPortalGraphEntry::BSPortalGraphEntry()
{
}
