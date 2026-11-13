// TESIdleForm type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and size follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESIdleForm.h.
// The destructor is declared without a body in this unit: the deleting destructor calls the plain one
// at RVA 0x3b6a20, which is bound by hint. The members are not recovered. Adapted bodies: none declared.
// TESIdleForm, TESIdleForm::~TESIdleForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESIdleForm::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 13, RVA 0x3b7240
// TESIdleForm::unk20: GUESS(low); stands for the members from 0x20 to 0x67
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESIdleForm : public TESForm {
public:
    TESIdleForm();
    ~TESIdleForm() override;  // 00
    void InitItemImpl() override;  // 13

    std::uint8_t unk20[0x48];  // 20
};
static_assert(sizeof(TESIdleForm) == 0x68, "layout");
