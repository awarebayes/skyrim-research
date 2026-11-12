// Type declarations for the InventoryChanges translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/I/InventoryChanges.h,
// include/RE/I/InventoryEntryData.h, include/RE/B/BGSOutfit.h. No NG code is copied; the
// declarations below are minimal stand-ins that reproduce only what the compared functions use.
// InventoryChanges, IItemChangeVisitor, InventoryEntryData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Names are unverified. Only the layouts the functions read were checked against the image.
#pragma once

#include <cstdint>

// BSSimpleList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
template <class T>
struct BSSimpleList {
    T              item;  // 0x00
    BSSimpleList*  next;  // 0x08
};

// BSTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
template <class T>
struct BSTArray {
    void*         allocator;  // 0x00
    T*            data;       // 0x08
    std::uint32_t capacity;   // 0x10
    std::uint32_t pad14;
    std::uint32_t size;       // 0x18
};

// TESForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESForm {
public:
    std::uint8_t pad00[0x1a];
    std::uint8_t formType;  // 0x1A
};

// TESBoundObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESBoundObject : public TESForm {
};

// BGSOutfit: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class BGSOutfit : public TESForm {
public:
    std::uint8_t        pad1b[0x20 - 0x1b];
    BSTArray<TESForm*>  outfitItems;  // 0x20
};

// ExtraDataList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class ExtraDataList;

// InventoryEntryData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class InventoryEntryData {
public:
    TESBoundObject*                  object;      // 0x00
    BSSimpleList<ExtraDataList*>*    extraLists;  // 0x08
    std::int32_t                     countDelta;  // 0x10
};

// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESObjectREFR;

// InventoryUtils InventoryUtils::ItemFilter: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the class name is in the image's RTTI and in NG's RTTI and VTABLE offset lists (RTTI_InventoryUtils__ItemFilter, VTABLE_InventoryUtils__ItemFilter); NG declares no class
// InventoryUtils::ItemFilter::~ItemFilter: GUESS(low); the function at RVA 0x22b710 only stores the vftable pointer and returns, as an out-of-line base-class destructor does
// InventoryUtils::ItemFilter::Unk_01: GUESS; placeholder for the unknown second virtual slot
namespace InventoryUtils {
class ItemFilter {
public:
    virtual ~ItemFilter();
    virtual void Unk_01() = 0;
};
}

class InventoryChanges {
public:
    // IItemChangeVisitor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    class IItemChangeVisitor {
    public:
        virtual ~IItemChangeVisitor();
        virtual std::uint32_t Visit(InventoryEntryData* a_entryData) = 0;  // slot 1, 1 means continue
    };

    void VisitInventory(IItemChangeVisitor& visitor);
    void InitOutfitItems(BGSOutfit* a_outfit, std::uint16_t a_npcLevel);

    BSSimpleList<InventoryEntryData*>* entryList;  // 0x00
    TESObjectREFR*                     owner;      // 0x08
};

// OutfitItemCapture, ForEachOutfitItemGuess: GUESS
// The callee at RVA 0x23fa80 has no community name.
// InitOutfitItems hands it the outfit's item array and a small capture block (outfit, this, level).
struct OutfitItemCapture {
    BGSOutfit*         outfit;  // 0x00
    InventoryChanges*  self;    // 0x08
    std::uint16_t      level;   // 0x10
};
void ForEachOutfitItemGuess(BSTArray<TESForm*>* a_items, OutfitItemCapture& a_capture);
