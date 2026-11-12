// BGSKeyword type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSKeyword, BGSKeyword::GetFormEditorID, BGSKeyword::formEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSFixedString, BSFixedString::_data: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; only the string pointer at offset 0 is claimed, public here
#pragma once

#include <cstdint>

#include "TESForm.h"

class BSFixedString {
public:
    const char* _data;  // 00
};

class BGSKeyword : public TESForm {
public:
    const char* GetFormEditorID() const override;  // 32

    BSFixedString formEditorID;  // 20
};
