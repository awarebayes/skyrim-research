// BGSStoryManagerEventNode InitializeData and GetFormEditorID, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s05-tesform-bgsstorymanagereventnode
// RVA 0x535c10, 28 bytes (InitializeData); RVA 0x535d60, 39 bytes (GetFormEditorID).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names and the GetFormEditorID shape from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// The call in InitializeData (target 0x5360f0) is BGSStoryManagerNodeBase::InitializeData; the tail jump in
// GetFormEditorID (0x532f30) is BGSRegisteredStoryEvent::GetName; both are bound by position;
// the two string literals are bound by hint to their .rdata addresses.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its threshold.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Both functions above are compared.
#include "BGSStoryManagerEventNode.h"

void BGSStoryManagerEventNode::InitializeData()
{
    BGSStoryManagerNodeBase::InitializeData();
    event = nullptr;
}

const char* BGSStoryManagerEventNode::GetFormEditorID() const
{
    if (TestBit(formFlags, 3)) {
        if (event) {
            return event->GetName();
        }
        return "(No event)";
    }
    return "(Uninitialized event node)";
}
