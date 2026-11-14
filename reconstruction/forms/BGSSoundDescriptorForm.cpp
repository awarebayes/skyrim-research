// BGSSoundDescriptorForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgssounddescriptorform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-4 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x32a7c0, 25 bytes: BGSSoundDescriptorForm::SetFormEditorID
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSSoundDescriptorForm.h"

// SetEditorIDFromString: GUESS(low)
void SetEditorIDFromString(const char* a_str, BGSSoundDescriptorForm* a_form);

// RVA 0x32a7c0, 25 bytes, BGSSoundDescriptorForm::SetFormEditorID.
bool BGSSoundDescriptorForm::SetFormEditorID(const char* a_str)
{
    SetEditorIDFromString(a_str, this);
    return true;
}
