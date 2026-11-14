// TESImageSpaceModifiableForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesimagespacemodifiableform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1e8660, 3 bytes: TESImageSpaceModifiableForm::ClearDataComponent
//   RVA 0x1e8650, 9 bytes: TESImageSpaceModifiableForm::InitializeDataComponent
//   RVA 0x1e8760, 43 bytes: TESImageSpaceModifiableForm::~TESImageSpaceModifiableForm
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESImageSpaceModifiableForm.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESImageSpaceModifiableForm::TESImageSpaceModifiableForm()
{
}

// ClearDataComponent: the target has no work to do.
void TESImageSpaceModifiableForm::ClearDataComponent()
{
}

// InitializeDataComponent: the target clears the pointer at +0x8.
void TESImageSpaceModifiableForm::InitializeDataComponent()
{
    data08 = nullptr;
}
