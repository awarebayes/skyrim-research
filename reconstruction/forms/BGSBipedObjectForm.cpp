// BGSBipedObjectForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsbipedobjectform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1d20f0, 3 bytes: BGSBipedObjectForm::ClearDataComponent
//   RVA 0x1d20e0, 8 bytes: BGSBipedObjectForm::InitializeDataComponent
//   RVA 0x1d21f0, 43 bytes: BGSBipedObjectForm::~BGSBipedObjectForm
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSBipedObjectForm.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSBipedObjectForm::BGSBipedObjectForm()
{
}

// Compared function: RVA 0x1d20f0, 3 bytes, BGSBipedObjectForm::ClearDataComponent.
void BGSBipedObjectForm::ClearDataComponent()
{
}

// Compared function: RVA 0x1d20e0, 8 bytes, BGSBipedObjectForm::InitializeDataComponent.
void BGSBipedObjectForm::InitializeDataComponent()
{
    unk08 = 0;
}

// Compared as the scalar deleting destructor; the sized delete it calls is bound by RVA in
// bind-hints.json.
BGSBipedObjectForm::~BGSBipedObjectForm()
{
}
