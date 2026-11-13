// BSTempEffectSimpleDecal functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bstempeffectsimpledecal
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x4b2950, 5 bytes: BSTempEffectSimpleDecal::Get3D
//   RVA 0x4b1090, 35 bytes: BSTempEffectSimpleDecal::Initialize
//   RVA 0x4b4a40, 52 bytes: BSTempEffectSimpleDecal::~BSTempEffectSimpleDecal
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSTempEffectSimpleDecal.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSTempEffectSimpleDecal::BSTempEffectSimpleDecal(TESObjectCELL* a_cell, float a_lifetime)
    : BSTempEffect(a_cell, a_lifetime)
{
}

// Body done: RVA 0x4b2950, 5 bytes, BSTempEffectSimpleDecal::Get3D.
NiAVObject* BSTempEffectSimpleDecal::Get3D() const
{
    return effect3D;
}

// Body done: RVA 0x4b1090, 35 bytes, BSTempEffectSimpleDecal::Initialize. The flag is set only
// when the shape setup succeeds.
void BSTempEffectSimpleDecal::Initialize()
{
    if (SetupAVShape(avShape)) {
        initialized = true;
    }
}

// RVA 0x4b4a40 (scalar deleting destructor) has no body here: the compiler emits the deleting form
// and calls the complete destructor, which attempt binds to the listed address.
