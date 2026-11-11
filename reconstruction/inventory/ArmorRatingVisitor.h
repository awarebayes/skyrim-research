// Type declarations for the ArmorRatingVisitor translation unit (build sse-steam-1-7-104).
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/A/ArmorRatingVisitor.h,
// include/RE/A/ArmorRatingVisitorBase.h, include/RE/B/BSTArray.h. No NG code is copied; these
// are minimal stand-ins that reproduce only the offsets the reconstructed function reads.
// Names are COMMUNITY and unverified; the class name and vftable slot 4 agree with EXE_RTTI.
// Only the two offsets the function reads (armors data at 0x28, size at 0x38) were checked
// against the image; the other members are NG's layout, kept to place those two correctly.
//
// The original class lives in an anonymous namespace. This one has external linkage because
// comparator contract v1 needs the compared function as an external symbol in its own COMDAT.
// ArmorRatingVisitorBase is declared separately, as in NG, because Visit is its member. Its
// interface base InventoryChanges::IItemChangeVisitor is not declared; the base class here is a
// stand-in that only places the virtual slots and members the compared functions use. The
// other classes below (TESBoundObject, TESObjectARMO, InventoryEntryData, BSScrapArray) are
// per-unit stand-ins as well.
#pragma once

#include <cstdint>

class Actor;

// Minimal stand-ins; only the offsets the compared functions read are real (GUESS names).
class TESBoundObject {
public:
    std::uint8_t pad00[0x1a];
    std::uint8_t formType;  // 0x1A, 0x1A means armor
};

class TESObjectARMO : public TESBoundObject {
public:
    std::uint8_t  pad1b[0x1bc - 0x1b];
    std::int32_t  unk1BC;  // 0x1BC, compared against 2; meaning unknown
};

class InventoryEntryData {
public:
    TESBoundObject* object;  // 0x00
};

// Callee 0x27edf0 has no community name; GUESS name. Visit picks the rating at 0x18 when it returns 12.
std::int32_t GetArmorKind(TESObjectARMO* a_armor);
// COMMUNITY (CommonLibSSE-NG b93280e, MIT): RE::GetArmorFinalRating, AE id 16017.
float GetArmorFinalRating(InventoryEntryData* a_entry, float a_armorPerks, float a_skillMultiplier);
// COMMUNITY (CommonLibSSE-NG b93280e, MIT): BGSEntryPoint::HandleEntryPoint, AE id 23526; the
// template is instantiated here with the argument list this call site uses.
void HandleEntryPoint(std::uint32_t a_entryPoint, Actor* a_perkOwner, TESObjectARMO* a_armor, float* a_value);

template <class T>
struct BSScrapArray {
    void*         allocator;  // 0x00
    T*            data;       // 0x08
    std::uint32_t capacity;   // 0x10
    std::uint32_t pad14;
    std::uint32_t size;       // 0x18

    std::uint32_t Size() const { return size; }
    T&            operator[](std::uint32_t i) { return data[i]; }
};

// COMMUNITY (CommonLibSSE-NG b93280e, MIT): ArmorRatingVisitorBase, a subclass of
// InventoryChanges::IItemChangeVisitor. The interface base is reduced here to the vftable slots 1
// to 3 that precede the added virtuals; slots 2 and 3 are GUESS placeholders.
class ArmorRatingVisitorBase {
public:
    virtual ~ArmorRatingVisitorBase();
    virtual std::uint32_t Visit(InventoryEntryData* a_entryData);  // slot 1
    virtual void          Unk02();
    virtual void          Unk03();
    virtual bool          HaveNotVisitedArmor(TESObjectARMO* a_armor);  // slot 4
    virtual void          VisitArmor(TESObjectARMO* a_armor);           // slot 5

    Actor*                        actor;             // 0x08
    float                         armorSum;          // 0x10
    float                         armorPerks;        // 0x14
    float                         lightArmorRating;  // 0x18
    float                         heavyArmorRating;  // 0x1C
};

class ArmorRatingVisitor : public ArmorRatingVisitorBase {
public:
    ~ArmorRatingVisitor() override;
    bool HaveNotVisitedArmor(TESObjectARMO* a_armor) override;

    BSScrapArray<TESObjectARMO*>  armors;            // 0x20
};
