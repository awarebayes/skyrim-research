// BGSPreloadable functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgspreloadable
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-4), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x2601d0, 3 bytes: BGSPreloadable::ClearDataComponent
//   RVA 0x2601e0, 3 bytes: BGSPreloadable::CopyComponent
//   RVA 0x2601f0, 3 bytes: BGSPreloadable::InitializeDataComponent
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSPreloadable.h"

// Body done: RVA 0x2601d0, 3 bytes, BGSPreloadable::ClearDataComponent.
void BGSPreloadable::ClearDataComponent()
{
}

// Body done: RVA 0x2601e0, 3 bytes, BGSPreloadable::CopyComponent.
void BGSPreloadable::CopyComponent(BaseFormComponent* a_rhs)
{
}

// Body done: RVA 0x2601f0, 3 bytes, BGSPreloadable::InitializeDataComponent.
void BGSPreloadable::InitializeDataComponent()
{
}
