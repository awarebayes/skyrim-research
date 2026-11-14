// TESTexture1024::GetMaxAllowedSize, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x309f20, 6 bytes (GetMaxAllowedSize).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The one function above is compared.
#include "TESTexture1024.h"

// TESTexture1024::TESTexture1024: GUESS(low); defined so the vftable and the deleting destructor are emitted
TESTexture1024::TESTexture1024()
{
}

std::uint32_t TESTexture1024::GetMaxAllowedSize()
{
    return 1024;
}
