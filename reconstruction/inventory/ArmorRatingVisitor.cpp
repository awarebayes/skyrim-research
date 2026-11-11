// ArmorRatingVisitor::HaveNotVisitedArmor, build sse-steam-1-7-104, RVA 0x73ad90, 84 bytes.
//
// Evidence: reports/sse-steam-1-7-104/0x73ad90.json and findings/first-function.md.
// Source exposure: mixed. Drafted by a model worker (claude-sonnet-5-5) from a local instruction
// listing and decompiler output of the pinned image, with types from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method name or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Only HaveNotVisitedArmor is compared. The destructor exists so the class has a vftable and the
// function is emitted out of line; it is not claimed to match the game's destructor.
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

ArmorRatingVisitor::~ArmorRatingVisitor() {}
