// BGSStoryManagerQuestNode::Revert, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s05-tesform-bgsstorymanagerquestnode
// RVA 0x539020, 40 bytes (Revert).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its threshold.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Revert is compared.
#include "BGSStoryManagerQuestNode.h"

void BGSStoryManagerQuestNode::Revert(BGSLoadFormBuffer*)
{
    for (std::uint32_t i = 0; i < quests.size; ++i) {
        childrenLastRun.data[i] = 0.0f;
    }
}
