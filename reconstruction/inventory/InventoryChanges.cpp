// Build sse-steam-1-7-104. Compared functions:
//   RVA 0x22b710, 11 bytes: out-of-line destructor of an ItemFilter-like interface. The code
//     contradicts the community name InventoryChanges::GetItemCount: it only stores a vftable
//     pointer and returns.
//   RVA 0x233f90, 44 bytes: InitOutfitItems.
//   RVA 0x2372c0, 58 bytes: VisitInventory.
// InitOutfitItems, VisitInventory: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// InventoryUtils::ItemFilter::~ItemFilter: GUESS(low)
//
// Labels: v2
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local instruction listing and
// decompiler output of the pinned image, with types from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Compared: the functions listed above. The destructor of the ItemFilter stand-in exists so that
// class has a vftable.
#include "InventoryChanges.h"

// The community name for RVA 0x22b710 (InventoryChanges::GetItemCount) does not fit a function
// that only stores a vftable pointer; the destructor identity is labelled in the header.
InventoryUtils::ItemFilter::~ItemFilter() {}

void InventoryChanges::InitOutfitItems(BGSOutfit* a_outfit, std::uint16_t a_npcLevel)
{
    if (a_outfit) {
        OutfitItemCapture capture{ a_outfit, this, a_npcLevel };
        ForEachOutfitItemGuess(&a_outfit->outfitItems, capture);
    }
}

void InventoryChanges::VisitInventory(IItemChangeVisitor& visitor)
{
    auto*         node = entryList;
    // Never read: every pass assigns result before the loop condition tests it.
    std::uint32_t result = 1;
    do {
        if (!node) {
            return;
        }
        InventoryEntryData* entry = node->item;
        if (!entry) {
            return;
        }
        node = node->next;
        result = visitor.Visit(entry);
    } while (result == 1);
}
