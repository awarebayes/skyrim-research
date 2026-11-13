// BSProceduralLightningTasklet functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s16-bstaskletdata-bsprocedurallightningtasklet
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xffe8e0, 8 bytes: BSProceduralLightningTasklet::OnComplete
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSProceduralLightningTasklet.h"

void BSProceduralLightningTasklet::OnComplete()
{
    field_ac = true;
}
