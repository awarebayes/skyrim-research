// Actor::HasOutfitItems, build sse-steam-1-7-104.
//
// RVA 0x2e7fc0, 156 bytes.
// Evidence: findings/second-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local listing of the pinned image
// with types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Only HasOutfitItems is compared. The callee at RVA 0x1648b0 is declared as FindOutfitExtra, a
// GUESS. A byte match shows this source and recipe produce the checked code; it does not verify
// the community name or that the original source looked like this.
#include "Actor.h"

bool Actor::HasOutfitItems(BGSOutfit* a_outfit)
{
    if (a_outfit) {
        InventoryChanges* changes = MakeInventoryChanges();
        std::uint32_t     id      = a_outfit->formID;
        for (auto* entries = changes->entryList; entries && entries->item; entries = entries->next) {
            for (auto* lists = entries->item->extraLists; lists && (lists->next || lists->item);
                 lists       = lists->next) {
                OutfitExtra* extra = FindOutfitExtra(lists->item);
                if (extra && (id == 0 || extra->outfitID == id)) {
                    return true;
                }
            }
        }
    }
    return false;
}
