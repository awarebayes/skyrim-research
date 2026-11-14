// BGSKeywordForm functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgskeywordform
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x14c8b0, 3 bytes: BGSKeywordForm::GetDefaultKeyword
//   RVA 0x1d8690, 3 bytes: BGSKeywordForm::InitializeDataComponent
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSKeywordForm.h"

// GetDefaultKeyword: the target returns a null pointer.
BGSKeyword* BGSKeywordForm::GetDefaultKeyword() const
{
    return nullptr;
}

// InitializeDataComponent: the target has no work to do.
void BGSKeywordForm::InitializeDataComponent()
{
}
