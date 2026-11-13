// BSFlattenedBoneTree functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsflattenedbonetree
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xef4d10, 27 bytes: BSFlattenedBoneTree::UpdateDownwardPass
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSFlattenedBoneTree.h"

void BSFlattenedBoneTree::UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2)
{
    NiNode::UpdateDownwardPass(a_data, a_arg2);
    UpdateBoneRoots();
}
