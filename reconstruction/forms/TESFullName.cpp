// TESFullName::GetFullName, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x146720, 9 bytes (GetFullName).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The one function above is compared.
#include "TESFullName.h"

void TESFullName::ClearDataComponent()
{
}

std::uint32_t TESFullName::GetFullNameLength() const
{
    return BSFixedStringLength(&fullName);
}

const char* TESFullName::GetFullName() const
{
    return fullName.data();
}
