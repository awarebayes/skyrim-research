// BGSFootstep type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSFootstep, BGSFootstep::~BGSFootstep, BGSFootstep::tag, BGSFootstep::impactSet: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSFixedString, BSFixedString::~BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; a single string pointer, the destructor is declared and not defined and bound by hint to 0xeb1100
// BSFixedString::_data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG keeps it private
// BGSImpactDataSet: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
// BGSFootstep::BGSFootstep: GUESS(low); the implicit constructor, defined only so the unit emits the vftable and the deleting destructor
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSImpactDataSet;

class BSFixedString {
public:
    ~BSFixedString();

    const char* _data;  // 00
};

class BGSFootstep : public TESForm {
public:
    BGSFootstep();

    BSFixedString     tag;        // 20
    BGSImpactDataSet* impactSet;  // 28
};
static_assert(sizeof(BGSFootstep) == 0x30, "layout");
