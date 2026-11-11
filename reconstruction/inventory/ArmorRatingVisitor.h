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
// ArmorRatingVisitorBase is folded into this class: the base adds no code the compared
// function depends on, and its members are declared here at the same offsets.
#pragma once

#include <cstdint>

class TESObjectARMO;
class Actor;

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

class ArmorRatingVisitor {
public:
    virtual ~ArmorRatingVisitor();
    virtual bool HaveNotVisitedArmor(TESObjectARMO* a_armor);

    Actor*                        actor;             // 0x08
    float                         armorSum;          // 0x10
    float                         armorPerks;        // 0x14
    float                         lightArmorRating;  // 0x18
    float                         heavyArmorRating;  // 0x1C
    BSScrapArray<TESObjectARMO*>  armors;            // 0x20
};
