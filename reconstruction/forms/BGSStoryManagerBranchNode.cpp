// BGSStoryManagerBranchNode accessors and InitItemImpl, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s05-tesform-bgsstorymanagerbranchnode
// RVA 0x1c8500, 4 bytes (QChildCount); RVA 0x1c7cd0, 11 bytes (GetChild); RVA 0x5358d0, 29 bytes (InitItemImpl).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// The calls in InitItemImpl (targets 0x5363e0, BGSStoryManagerNodeBase::InitItemImpl, and 0x1e60b0,
// SetFormFlag) are bound by position.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its threshold.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. All three functions above are compared.
#include "BGSStoryManagerBranchNode.h"

std::uint32_t BGSStoryManagerBranchNode::QChildCount() const
{
    return children.size;
}

BGSStoryManagerTreeForm* BGSStoryManagerBranchNode::GetChild(std::uint32_t a_idx) const
{
    return children.data[a_idx];
}

void BGSStoryManagerBranchNode::InitItemImpl()
{
    BGSStoryManagerNodeBase::InitItemImpl();
    SetFormFlag(true);
}
