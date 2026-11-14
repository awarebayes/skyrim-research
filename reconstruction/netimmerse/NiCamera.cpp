// NiCamera functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nicamera
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611131358-2).
// Compared functions:
//   RVA 0xef1770, 27 bytes: NiCamera::UpdateWorldData
//   RVA 0xef1950, 37 bytes: NiCamera::UpdateWorldBound
//   RVA 0xef1a10, 62 bytes: NiCamera::~NiCamera
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiCamera.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared.
NiCamera::NiCamera()
{
}

// UpdateWorldData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
void NiCamera::UpdateWorldData()
{
    BaseUpdateWorldData();
    UpdateCameraWorldData();
}

// UpdateWorldBound: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
void NiCamera::UpdateWorldBound()
{
    worldBoundCopyA = worldBoundA;
    worldBoundCopyB = worldBoundB;
    worldBoundCopyC = worldBoundC;
}
