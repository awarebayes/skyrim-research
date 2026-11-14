// TESQualityForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesqualityform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-4), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1ef660, 3 bytes: TESQualityForm::ClearDataComponent
//   RVA 0x1ef650, 8 bytes: TESQualityForm::InitializeDataComponent
//   RVA 0x1ef6e0, 43 bytes: TESQualityForm::~TESQualityForm (scalar deleting destructor; the destructor
//   is an empty inline body in the header)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESQualityForm.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESQualityForm::TESQualityForm()
{
}

// Body done: RVA 0x1ef660, 3 bytes, TESQualityForm::ClearDataComponent.
void TESQualityForm::ClearDataComponent()
{
}

// Body done: RVA 0x1ef650, 8 bytes, TESQualityForm::InitializeDataComponent.
void TESQualityForm::InitializeDataComponent()
{
    value08 = 0;
}
