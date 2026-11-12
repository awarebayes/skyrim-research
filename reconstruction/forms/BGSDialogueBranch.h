// BGSDialogueBranch type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSDialogueBranch, BGSDialogueBranch::InitializeData, ::flags, ::pad24, ::quest, ::startingTopic: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESQuest, TESTopic: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESQuest;
class TESTopic;

class BGSDialogueBranch : public TESForm {
public:
    void InitializeData() override;  // 04

    std::uint32_t flags;          // 20
    std::uint32_t pad24;          // 24
    TESQuest*     quest;          // 28
    TESTopic*     startingTopic;  // 30
};
