// BGSOutfit functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsoutfit
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by gpt-6.1-sol, Engineer p105 box2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x264820, 108 bytes: BGSOutfit::ClearData
//   RVA 0x264d80, 223 bytes: BGSOutfit::~BGSOutfit
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSOutfit.h"
extern __declspec(thread) std::uint32_t OutfitTLS;
struct OutfitScope {
    std::uint32_t saved;
    OutfitScope() : saved(OutfitTLS) { OutfitTLS=0x65; }
    ~OutfitScope() { OutfitTLS=saved; }
};
void BGSOutfit::ClearData() {
    OutfitScope scope;
    // array: GUESS(low); hold the represented member address across cleanup.
    auto* array=&items;
    if (array->data) { ClearOutfitArray(array); array->count=0; }
}
