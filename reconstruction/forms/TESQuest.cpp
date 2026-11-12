// TESQuest accessors, InitializeData, FinishLoadGame and destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s05-tesform-tesquest
// RVA 0x3dfeb0, 8 bytes (QConditions); RVA 0x3df9b0, 22 bytes (GetFormEditorID); RVA 0x3d2870, 42 bytes (FinishLoadGame); RVA 0x3ce410, 48 bytes (InitializeData);
// RVA 0x3dedb0, 52 bytes (~TESQuest, the deleting destructor).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// Unnamed callees, bound by position or by hint: 0x3ce190 is the plain destructor, declared and not defined
// here; 0x15a743c is the global sized operator delete; 0x1e5840 is TESForm::FinishLoadGame; 0x204250 is
// QueuedPromoteQuestTask::Finish; the empty string at 0x1b58020 is the literal in BSString::c_str.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its threshold.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The four functions other than GetFormEditorID are compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "TESQuest.h"

// Not compared: defined so that this unit emits the vftable and with it the deleting destructor.
TESQuest::TESQuest()
{
}

TESCondition* TESQuest::QConditions()
{
    return &objConditions;
}

const char* TESQuest::GetFormEditorID() const
{
    return formEditorID.c_str();
}

void TESQuest::FinishLoadGame(BGSLoadFormBuffer* a_buf)
{
    TESForm::FinishLoadGame(a_buf);
    if (promoteTask) {
        promoteTask->Finish();
    }
}

void TESQuest::InitializeData()
{
    eventID = 0xFFFFFFFF;
    data.flags |= static_cast<std::uint16_t>(QuestFlag::kRunOnce);
    currentStage = 0;
    startEventData = nullptr;
    currentInstanceID = 0;
    alreadyRun = false;
}
