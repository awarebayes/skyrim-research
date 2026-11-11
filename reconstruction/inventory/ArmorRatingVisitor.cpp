// ArmorRatingVisitor::HaveNotVisitedArmor, build sse-steam-1-7-104, RVA 0x73ad90, 84 bytes.
// ArmorRatingVisitorBase::Visit (COMMUNITY name), RVA 0x73ae00, 172 bytes.
//
// Evidence: findings/first-function.md, findings/second-batch-selection.md.
// Source exposure: mixed. Drafted by a model worker (claude-sonnet-5-5) from a local instruction
// listing and decompiler output of the pinned image, with types from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method name or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Only HaveNotVisitedArmor and Visit are compared. The destructors exist so the classes have
// vftables and the functions are emitted out of line; the base class's Unk02, Unk03,
// HaveNotVisitedArmor and VisitArmor bodies exist only to complete the base vftable (the last two
// follow NG's header comments). None of these is compared or claimed to match the game.
#include "ArmorRatingVisitor.h"

bool ArmorRatingVisitor::HaveNotVisitedArmor(TESObjectARMO* a_armor)
{
    std::int32_t idx = -1;
    for (std::uint32_t i = 0; i < armors.Size() && idx == -1; ++i) {
        if (armors[i] == a_armor) {
            idx = static_cast<std::int32_t>(i);
        }
    }
    return idx == -1;
}

std::uint32_t ArmorRatingVisitorBase::Visit(InventoryEntryData* a_entryData)
{
    TESBoundObject* object = a_entryData->object;
    if (object && object->formType == 0x1a) {
        auto* armor = static_cast<TESObjectARMO*>(object);
        if (armor->unk1BC != 2 && HaveNotVisitedArmor(armor)) {
            float skill = GetArmorKind(armor) == 0xc ? lightArmorRating : heavyArmorRating;
            float rating = GetArmorFinalRating(a_entryData, armorPerks, skill);
            HandleEntryPoint(0x55, actor, armor, &rating);
            armorSum += rating;
            VisitArmor(armor);
        }
    }
    return 1;
}

ArmorRatingVisitor::~ArmorRatingVisitor() {}

ArmorRatingVisitorBase::~ArmorRatingVisitorBase() {}
void ArmorRatingVisitorBase::Unk02() {}
void ArmorRatingVisitorBase::Unk03() {}
bool ArmorRatingVisitorBase::HaveNotVisitedArmor(TESObjectARMO*) { return true; }
void ArmorRatingVisitorBase::VisitArmor(TESObjectARMO*) {}
