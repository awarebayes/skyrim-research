// NiDefaultAVObjectPalette functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-nidefaultavobjectpalette
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf011d0, 5 bytes: NiDefaultAVObjectPalette::SetScene
//   RVA 0xf00a10, 83 bytes: NiDefaultAVObjectPalette::~NiDefaultAVObjectPalette
// Functions set aside in near-miss/ (not in this unit): 0xf01190 SetAVObject, 0xf00a70 GetAVObject,
// 0xf002d0 ResetAndFillFromScenegraph.
// Adapted bodies: NiDefaultAVObjectPalette::SetScene, from powerof3/CommonLibSSE@654e55f
// include/RE/N/NiDefaultAVObjectPalette.h:28 (GPL-3.0, stated above); the body is one member store.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiDefaultAVObjectPalette.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiDefaultAVObjectPalette::NiDefaultAVObjectPalette()
{
}

void NiDefaultAVObjectPalette::SetScene(NiAVObject* a_scene)
{
    scene = a_scene;
}

// Body done: RVA 0xf00a10, 83 bytes, NiDefaultAVObjectPalette::~NiDefaultAVObjectPalette; compared
// as the scalar deleting destructor. The target does the NiRefObject cleanup itself, so keep this
// empty definition and the constructor: the inline base destructors in the header make the compiler
// produce the same body.
NiDefaultAVObjectPalette::~NiDefaultAVObjectPalette()
{
}

// Retained generated leaf; its byte-match evidence is renewed with this unit.
// Slot41: GUESS(low); method name inferred from vtable owner and slot
void* NiDefaultAVObjectPalette::Slot41() const
{
    return scene;
}
