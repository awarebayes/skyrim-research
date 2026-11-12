// TESTopicInfo::LoadGame and Revert, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x3f3150, 42 bytes (LoadGame).
// RVA 0x3f3180, 42 bytes (Revert).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESTopicInfo.h"

void TESTopicInfo::LoadGame(BGSLoadFormBuffer* a_buf)
{
    TESForm::LoadGame(a_buf);
    if (static_cast<std::int32_t>(a_buf->changeFlags) < 0) {
        saidOnce = true;
    }
}

void TESTopicInfo::Revert(BGSLoadFormBuffer* a_buf)
{
    TESForm::Revert(a_buf);
    if (static_cast<std::int32_t>(a_buf->oldChangeFlags) < 0) {
        saidOnce = false;
    }
}
