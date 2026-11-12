// TESWaterForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT):
// include/RE/T/TESWaterForm.h. TESForm comes from the shared header TESForm.h.
// TESWaterForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESWaterForm::GetDangerous, ::flags, ::alpha: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESWaterForm::unk20, ::unkBA: GUESS(low); regions the compared code does not touch; the TESFullName
// and TESAttackDamageForm bases at 0x20 and 0x30 and the later members are not modelled here
// TESWaterForm::~TESWaterForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declared out of line, the target's deleting destructor calls the plain one
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESWaterForm : public TESForm {
public:
    TESWaterForm();
    ~TESWaterForm() override;  // 00

    bool GetDangerous() const override;  // 1B

    // members
    std::uint8_t unk20[0x98];   // 20
    std::int8_t  alpha;         // B8
    std::uint8_t flags;         // B9
    std::uint8_t unkBA[0x1A6];  // BA
};
static_assert(sizeof(TESWaterForm) == 0x260, "layout");
