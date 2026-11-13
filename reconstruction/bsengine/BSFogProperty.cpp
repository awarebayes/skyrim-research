// BSFogProperty functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsfogproperty
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x155c460, 62 bytes: BSFogProperty::~BSFogProperty (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSFogProperty.h"

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared.
BSFogProperty::BSFogProperty()
{
}
