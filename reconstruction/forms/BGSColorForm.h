// BGSColorForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSColorForm, BGSColorForm::InitializeData, BGSColorForm::color, BGSColorForm::flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFullName: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); size 0x10 and BaseFormComponent base only claimed
// TESFullName::fullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares BSFixedString, here an 8-byte pointer
// Color: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG packs it as RGBA bytes in one 32-bit word
// Color::value: GUESS(low); the 32-bit word
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESFullName : public BaseFormComponent {
public:
    void*         fullName;  // 08
};

struct Color {
    std::uint32_t value;  // 00
};

class BGSColorForm : public TESForm, public TESFullName {
public:
    void InitializeData() override;  // 04
    void ClearData() override;       // 05

    Color         color;  // 30
    std::uint32_t flags;  // 34
};
