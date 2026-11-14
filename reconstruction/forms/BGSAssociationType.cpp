// BGSAssociationType functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsassociationtype
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by gpt-6.1-sol, Engineer p105 box2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x389800, 109 bytes: BGSAssociationType::~BGSAssociationType
//   RVA 0x389430, 131 bytes: BGSAssociationType::InitializeData
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSAssociationType.h"
BGSAssociationType::BGSAssociationType() {}
BGSAssociationType::~BGSAssociationType() { TESForm::ClearData(); }
// current, rows, columns: GUESS(low); traverse the two association-name pairs.
void BGSAssociationType::InitializeData() {
    flags=0;
    auto* current=&names[0];
    for (std::size_t rows=2; rows; --rows) {
        for (std::size_t columns=2; columns; --columns) {
            *current=BSFixedString(nullptr);
            ++current;
        }
    }
}
