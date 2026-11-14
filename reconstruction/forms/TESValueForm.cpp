// TESValueForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesvalueform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1f34d0, 3 bytes: TESValueForm::ClearDataComponent
//   RVA 0x1f34c0, 8 bytes: TESValueForm::InitializeDataComponent
//   RVA 0x1f36d0, 43 bytes: TESValueForm::~TESValueForm
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESValueForm.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESValueForm::TESValueForm()
{
}

// Compared function: RVA 0x1f34d0, 3 bytes, TESValueForm::ClearDataComponent.
void TESValueForm::ClearDataComponent()
{
}

// Compared function: RVA 0x1f34c0, 8 bytes, TESValueForm::InitializeDataComponent.
void TESValueForm::InitializeDataComponent()
{
    unk08 = 0;
}

// Compared as the scalar deleting destructor; the sized delete it calls is bound by RVA in
// bind-hints.json.
TESValueForm::~TESValueForm()
{
}
