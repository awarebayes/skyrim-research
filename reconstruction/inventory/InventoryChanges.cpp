// Build sse-steam-1-7-104. Compared functions:
//   RVA 0x22b710, 11 bytes: out-of-line destructor of an ItemFilter-like interface. The code
//     contradicts the community name InventoryChanges::GetItemCount: it only stores a vftable
//     pointer and returns.
//   RVA 0x233f90, 44 bytes: InitOutfitItems.
//   RVA 0x2372c0, 58 bytes: VisitInventory.
//   RVA 0x237300, 262 bytes: VisitWornItems.
// InitOutfitItems, VisitInventory, VisitWornItems: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GetWeaponSlotMask, OccupiesWornSlot: GUESS; file-local helpers with no address of their own
// InventoryUtils::ItemFilter::~ItemFilter: GUESS(low)
//
// Labels: v2
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local instruction listing and
// decompiler output of the pinned image, with types from the header beside this file.
// VisitWornItems was finished by claude-opus-5-5 from the Drafter's near-miss.
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

// FormType::Light, FormType::Weapon, FormType::Ammo: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); their values 0x1F, 0x29 and 0x2A, held as the local constants below
// kLight, kWeapon, kAmmo: GUESS(high); local spellings of those three form types
namespace {
    constexpr std::uint32_t kLight  = 0x1F;
    constexpr std::uint32_t kWeapon = 0x29;
    constexpr std::uint32_t kAmmo   = 0x2A;

    // The biped slots a weapon's animation type maps to, -1 (every slot) when it has none.
    std::int32_t GetWeaponSlotMask(TESObjectWEAP* a_weapon)
    {
        std::int32_t       mask = -1;
        const std::int32_t slot = a_weapon->weaponData.animationType;
        if (slot != -1 && slot < 10) {
            mask = gWeaponSlotMasks[slot];
        }
        return mask;
    }

    // Whether a worn entry occupies an equipment slot: armor through its biped slots, weapons
    // through their animation type, ammunition always, and lights (held torches) without a slot.
    bool OccupiesWornSlot(InventoryEntryData* a_entry)
    {
        std::int32_t mask;
        if (BGSBipedObjectForm* biped = GetBipedObjectForm(a_entry->object)) {
            mask = biped->bipedModelData.bipedObjectSlots;
        } else {
            TESBoundObject* object = a_entry->object;
            if (!object) {
                return false;
            }
            switch (static_cast<std::uint32_t>(object->formType)) {
            case kLight:
                mask = 0;
                break;
            case kWeapon:
                mask = GetWeaponSlotMask(static_cast<TESObjectWEAP*>(object));
                break;
            case kAmmo:
                return true;
            default:
                mask = 0;
                break;
            }
        }
        return mask != 0 || (a_entry->object && a_entry->object->formType == kLight);
    }
}

void InventoryChanges::VisitWornItems(IItemChangeVisitor& visitor)
{
    auto*         node = entryList;
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
        bool worn = false;
        for (auto* lists = entry->extraLists; lists && lists->item && !worn; lists = lists->next) {
            worn = lists->item->IsWorn(true, false);
        }
        if (worn && OccupiesWornSlot(entry)) {
            result = visitor.Visit(entry);
        }
    } while (result == 1);
}
