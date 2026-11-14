// BGSOpenCloseForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsopencloseform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (Claude Haiku 5.5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x267670, 3 bytes: BGSOpenCloseForm::Unk_03
//   RVA 0x2677e0, 3 bytes: BGSOpenCloseForm::HandleClose
//   RVA 0x2677f0, 3 bytes: BGSOpenCloseForm::HandleOpen
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSOpenCloseForm.h"

// Unk_03: the listing returns false.
bool BGSOpenCloseForm::Unk_03()
{
    return false;
}

// HandleClose: the listing is a bare return; there is no work to do.
void BGSOpenCloseForm::HandleClose(TESObjectREFR* a_target, TESObjectREFR* a_activator)
{
}

// HandleOpen: the listing is a bare return; there is no work to do.
void BGSOpenCloseForm::HandleOpen(TESObjectREFR* a_target, TESObjectREFR* a_activator)
{
}
