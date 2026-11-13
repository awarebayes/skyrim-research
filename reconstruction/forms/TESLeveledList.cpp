// TESLeveledList accessors and InitializeDataComponent, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1e88f0, 9 bytes (GetMultCalc); RVA 0x1e8930, 10 bytes (GetUseAll);
// RVA 0x1e8850, 18 bytes (InitializeDataComponent); RVA 0x1e8880, 20 bytes (GetChanceNone).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESLeveledList.h"

void TESLeveledList::InitializeDataComponent()
{
    entries = nullptr;
    chanceNone = 0;
    llFlags = 0;
    numEntries = 0;
    unk13 = 0;
    unk18 = nullptr;
    chanceGlobal = nullptr;
}

std::uint8_t TESLeveledList::GetChanceNone()
{
    if (chanceGlobal) {
        return static_cast<std::uint8_t>(chanceGlobal->value);
    }
    return chanceNone;
}

bool TESLeveledList::GetMultCalc()
{
    return TestBit(llFlags, 1);
}

bool TESLeveledList::GetUseAll()
{
    return TestBit(llFlags, 2);
}

std::int32_t TESLeveledList::GetLevDifferenceMax()
{
    return 0;
}
