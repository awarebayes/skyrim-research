// TESClass functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s02-tesform-tesclass
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3b2b10, 5 bytes: TESClass::GetMaximumTrainingLevel
//   RVA 0x3b2890, 44 bytes: TESClass::InitializeData
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESClass.h"

// g_defaultTrainingLevel: GUESS(low)
extern float g_defaultTrainingLevel;
// g_defaultTrainingSkill: GUESS(low)
extern std::uint32_t g_defaultTrainingSkill;

std::uint8_t TESClass::GetMaximumTrainingLevel()
{
    return maximumTrainingLevel;
}

void TESClass::InitializeData()
{
    volatile std::uint64_t* const zeroes = &unk50;
    zeroes[0] = 0;
    zeroes[1] = 0;
    zeroes[2] = 0;
    zeroes[3] = 0;
    unk70 = 0;
    trainingLevel = g_defaultTrainingLevel;
    trainingSkill = g_defaultTrainingSkill;
}
