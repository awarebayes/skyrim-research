// BGSStoryManagerQuestNode type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT):
// include/RE/B/BGSStoryManagerQuestNode.h, BGSStoryManagerNodeBase.h and BGSStoryManagerTreeForm.h.
// TESForm comes from the shared header TESForm.h; the story-manager base chain, BSTArray and TESQuest
// are stand-ins.
// BGSStoryManagerQuestNode, ::Revert, ::quests, ::numQuestsToStart, ::padC4, ::childrenLastRun: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSStoryManagerQuestNode::unk60: GUESS(low); stands for perQuestFlags and perQuestHoursUntilReset (two BSTHashMap at 60 and 90 in NG), not modelled
// BGSStoryManagerNodeBase, ::Flags, ::parent, ::previousSibling, ::maxQuests, ::flags, ::conditions, ::QConditions, ::InitializeData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSStoryManagerNodeBase::Flags::nodeFlags, ::questFags: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); plain 16-bit integers here
// BGSStoryManagerTreeForm, ::QChildCount, ::GetChild, ::QConditions, ::AcceptVisitor, ::lastVisitorID, ::pad24: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSStoryManagerTreeForm: EXE_RTTI; class name and base from the image RTTI
// BGSStoryManagerTreeVisitor, BGSStoryManagerTreeVisitor::VisitControl: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the type is needed for the slot signature
// BGSStoryManagerTreeForm::AcceptVisitor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; slot 3E, only the slot matters here
// TESCondition, TESCondition::head: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer, sized from the 0x48 class size
// BSTArray, BSTArray::data, ::capacity, ::size: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout (data, capacity, size) read from the listing, NG wraps it in an allocator
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

class BGSStoryManagerBranchNode;

class BGSStoryManagerNodeBase : public BGSStoryManagerTreeForm {
public:
    struct Flags {
        std::uint16_t nodeFlags;  // 0
        std::uint16_t questFags;  // 2
    };
    static_assert(sizeof(Flags) == 0x4, "layout");

    void          InitializeData() override;  // 04
    TESCondition* QConditions() override;     // 3D

    // members
    BGSStoryManagerBranchNode* parent;           // 28
    BGSStoryManagerNodeBase*   previousSibling;  // 30
    std::uint32_t              maxQuests;        // 38
    Flags                      flags;            // 3C
    TESCondition               conditions;       // 40
};
static_assert(sizeof(BGSStoryManagerNodeBase) == 0x48, "layout");

class TESQuest;

template <class T>
class BSTArray {
public:
    T*            data;      // 00
    std::uint32_t capacity;  // 08
    std::uint32_t pad0C;     // 0C
    std::uint32_t size;      // 10
    std::uint32_t pad14;     // 14
};
static_assert(sizeof(BSTArray<float>) == 0x18, "layout");

class BGSStoryManagerQuestNode : public BGSStoryManagerNodeBase {
public:
    void Revert(BGSLoadFormBuffer* a_buf) override;  // 12

    // members
    BSTArray<TESQuest*> quests;           // 48
    std::uint8_t        unk60[0x60];      // 60
    std::uint32_t       numQuestsToStart; // C0
    std::uint32_t       padC4;            // C4
    BSTArray<float>     childrenLastRun;  // C8
};
static_assert(sizeof(BGSStoryManagerQuestNode) == 0xE0, "layout");
