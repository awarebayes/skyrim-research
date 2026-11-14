// Hazard functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-hazard
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x7ee090, 3 bytes: Hazard::Unk_A3
//   RVA 0x7ee9c0, 3 bytes: Hazard::OnAddCellPerformQueueReference
//   RVA 0x7ee8d0, 29 bytes: Hazard::IsPermanent
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "Hazard.h"

void Hazard::Unk_A3()
{
}

bool Hazard::OnAddCellPerformQueueReference(TESObjectCELL& a_cell) const
{
    return false;
}

// The handler's temporary-ID test on this reference's form ID, negated.
bool Hazard::IsPermanent() const
{
    return !TESDataHandler::singleton->IsTemporaryFormID(formID);
}
