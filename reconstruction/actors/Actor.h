// Type declarations for the Actor::HasOutfitItems unit (build sse-steam-1-7-104).
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT)
// and are minimal stand-ins; no NG code is copied.
//   Actor, Actor::HasOutfitItems, BGSOutfit, TESObjectREFR::MakeInventoryChanges,
//   InventoryChanges, InventoryEntryData, ExtraDataList, BSSimpleList
//                       COMMUNITY (unverified)
//   BGSOutfit::formID   COMMUNITY name for the 32-bit word at offset 0x14 (TESForm::formID).
//   InventoryChanges::entryList   COMMUNITY name for the pointer at offset 0.
//   InventoryEntryData::extraLists  COMMUNITY name for the pointer at offset 8.
//   FindOutfitExtra, OutfitExtra, OutfitExtra::outfitID
//                       GUESS: the callee at RVA 0x1648b0 has no community name; it takes an
//                       ExtraDataList* and returns a record whose word at offset 0x10 is compared
//                       with the outfit's form id. Its real identity is not established.
//   Actor is declared with only the members this function needs; the base-class layout is not
//   reproduced, so the object layout of this stand-in is not claimed to match the game.
#pragma once

#include <cstdint>

template <class T>
struct BSSimpleList {
    T             item;  // 0x00
    BSSimpleList* next;  // 0x08
};

class ExtraDataList;

class InventoryEntryData {
public:
    void*                         object;      // 0x00
    BSSimpleList<ExtraDataList*>* extraLists;  // 0x08
};

class InventoryChanges {
public:
    BSSimpleList<InventoryEntryData*>* entryList;  // 0x00
};

class BGSOutfit {
public:
    std::uint8_t  unk00[0x14];
    std::uint32_t formID;  // 0x14
};

struct OutfitExtra {
    std::uint8_t  unk00[0x10];
    std::uint32_t outfitID;  // 0x10
};

// GUESS name; bound to RVA 0x1648b0.
OutfitExtra* FindOutfitExtra(ExtraDataList* a_list);

class Actor {
public:
    InventoryChanges* MakeInventoryChanges();
    bool              HasOutfitItems(BGSOutfit* a_outfit);
};
