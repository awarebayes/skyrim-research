// TESContainer: GetItemCount, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s04-baseformcomponent-tescontainer
// RVA 0x1e0b10, 43 bytes (GetItemCount);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "TESContainer.h"

std::int32_t TESContainer::GetItemCount(TESBoundObject* a_object) const
{
    std::int32_t total = 0;
    for (std::uint32_t i = 0; i < numContainerObjects; ++i) {
        if (containerObjects[i] && containerObjects[i]->obj == a_object) {
            total += containerObjects[i]->count;
        }
    }
    return total;
}

// TESContainer::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void TESContainer::InitializeDataComponent()
{
}
