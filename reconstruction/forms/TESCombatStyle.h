// TESCombatStyle type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and size follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESCombatStyle.h.
// The shape of the destructor follows the sibling's TESCombatStyle::~TESCombatStyle (an empty body;
// the base destructor runs after it). Members are not recovered. Adapted bodies: none declared.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/tescombatstyle.cpp (no line found; shape only, an empty destructor body)
// header-gap TESForm: the shared header lacks the helper at RVA 0x1e60b0, so a free function stands in.
// TESCombatStyle, TESCombatStyle::~TESCombatStyle, ::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESCombatStyle::unk20: GUESS(low); stands for the members from 0x20 to 0x9F
// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
// SetFormHelper: GUESS(low); the callee at RVA 0x1e60b0 taking the form and a bool, tail-called by InitItemImpl
#pragma once

#include <cstdint>

#include "TESForm.h"

void SetFormHelper(TESForm* a_form, bool a_set);

class TESCombatStyle : public TESForm {
public:
    TESCombatStyle();
    ~TESCombatStyle() override;  // 00

    void InitItemImpl() override;  // 13

    std::uint8_t unk20[0x80];  // 20
};
static_assert(sizeof(TESCombatStyle) == 0xA0, "layout");
