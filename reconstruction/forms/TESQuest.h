// TESQuest type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT):
// include/RE/T/TESQuest.h, BGSBaseAlias.h and BGSStoryManagerTreeForm.h. TESForm comes from the
// shared header TESForm.h; the other classes here are minimal stand-ins.
// TESQuest, ::QConditions, ::GetFormEditorID, ::FinishLoadGame, ::InitializeData, ::instanceData, ::currentInstanceID, ::aliases, ::data, ::eventID, ::objConditions, ::currentStage, ::alreadyRun, ::formEditorID, ::startEventData, ::promoteTask, ::promotedRefs, ::pad054, ::pad0E4, ::pad22B, ::pad22C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESQuest::~TESQuest: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declared out of line, the target's deleting destructor calls the plain one
// TESQuest::unk28, ::unk70, ::unkE8, ::unk110, ::unk220: GUESS(low); regions the compared code does not touch; TESFullName at 28 and the other members are not modelled
// TESQuest::promoteTask: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares NiPointer<QueuedPromoteQuestTask>, a raw pointer here
// QUEST_DATA, QUEST_DATA::flags, ::priority, ::questType, ::questDelayTime, QuestFlag, QuestFlag::kRunOnce: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); plain integers for the stl::enumeration members
// BGSBaseAlias, BGSBaseAlias::aliasName, ::owningQuest, ::aliasID: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSTArray, BSTArray::data, ::capacity, ::size: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout (data, capacity, size) read from the listings, NG wraps it in an allocator
// BSString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); data pointer first, the length fields are placeholders
// BSString::c_str: GUESS(low); NG declares c_str on BSStringT, the stand-in has it on BSString and returns an empty string for a null data pointer as the listing does
// QueuedPromoteQuestTask: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// QueuedPromoteQuestTask::Finish: GUESS(low); the target tail-jumps (0x204250) with the task as this
// BGSStoryManagerTreeForm, ::QChildCount, ::GetChild, ::QConditions, ::AcceptVisitor, ::lastVisitorID, ::pad24: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSStoryManagerTreeForm: EXE_RTTI; class name and base from the image RTTI
// BGSStoryManagerTreeVisitor, BGSStoryManagerTreeVisitor::VisitControl: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the type is needed for the slot signature
// BGSStoryManagerTreeForm::AcceptVisitor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; slot 3E, only the slot matters here
// TESCondition, TESCondition::head: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSStoryManagerTreeVisitor {
public:
    enum class VisitControl : std::int32_t {
    };
};

class TESCondition {
public:
    void* head;  // 00
};

class BGSStoryManagerTreeForm : public TESForm {
public:
    ~BGSStoryManagerTreeForm() override;  // 00

    virtual std::uint32_t                            QChildCount() const;                                       // 3B
    virtual BGSStoryManagerTreeForm*                 GetChild(std::uint32_t a_idx) const;                       // 3C
    virtual TESCondition*                            QConditions() = 0;                                         // 3D
    virtual BGSStoryManagerTreeVisitor::VisitControl AcceptVisitor(BGSStoryManagerTreeVisitor& a_visitor) = 0;  // 3E

    // members
    std::uint32_t lastVisitorID;  // 20
    std::uint32_t pad24;          // 24
};
static_assert(sizeof(BGSStoryManagerTreeForm) == 0x28, "layout");


template <class T>
class BSTArray {
public:
    T*            data;      // 00
    std::uint32_t capacity;  // 08
    std::uint32_t pad0C;     // 0C
    std::uint32_t size;      // 10
    std::uint32_t pad14;     // 14
};
static_assert(sizeof(BSTArray<void*>) == 0x18, "layout");

class BSString {
public:
    const char* c_str() const
    {
        return data ? data : "";
    }

    char*         data;      // 00
    std::uint16_t dataLen;   // 08
    std::uint16_t bufLen;    // 0A
    std::uint32_t pad0C;     // 0C
};
static_assert(sizeof(BSString) == 0x10, "layout");

class TESQuest;

class BGSBaseAlias {
public:
    virtual ~BGSBaseAlias();  // 00

    void*         aliasName;    // 08
    TESQuest*     owningQuest;  // 10
    std::uint32_t aliasID;      // 18
    std::uint32_t pad1C;        // 1C
};

class QueuedPromoteQuestTask {
public:
    void Finish();
};

struct QUEST_DATA {
    float         questDelayTime;  // 0
    std::uint16_t flags;           // 4
    std::int8_t   priority;        // 6
    std::uint8_t  questType;       // 7
};
static_assert(sizeof(QUEST_DATA) == 0x8, "layout");

enum class QuestFlag : std::uint16_t {
    kRunOnce = 1 << 8
};

class TESQuest : public BGSStoryManagerTreeForm {
public:
    TESQuest();
    ~TESQuest() override;  // 00

    void          InitializeData() override;                       // 04
    void          FinishLoadGame(BGSLoadFormBuffer* a_buf) override;  // 11
    const char*   GetFormEditorID() const override;                // 32
    TESCondition* QConditions() override;                          // 3D

    // members
    std::uint8_t            unk28[0x10];      // 28
    BSTArray<void*>         instanceData;     // 38
    std::uint32_t           currentInstanceID;  // 50
    std::uint32_t           pad054;           // 54
    BSTArray<BGSBaseAlias*> aliases;          // 58
    std::uint8_t            unk70[0x68];      // 70
    QUEST_DATA              data;             // D8
    std::uint32_t           eventID;          // E0
    std::uint32_t           pad0E4;           // E4
    std::uint8_t            unkE8[0x20];      // E8
    TESCondition            objConditions;    // 108
    std::uint8_t            unk110[0x110];    // 110
    void*                   unk220;           // 220
    std::uint16_t           currentStage;     // 228
    bool                    alreadyRun;       // 22A
    std::uint8_t            pad22B;           // 22B
    std::uint32_t           pad22C;           // 22C
    BSString                formEditorID;     // 230
    const void*             startEventData;   // 240
    QueuedPromoteQuestTask* promoteTask;      // 248
    BSTArray<std::uint32_t> promotedRefs;     // 250
};
static_assert(sizeof(TESQuest) == 0x268, "layout");
