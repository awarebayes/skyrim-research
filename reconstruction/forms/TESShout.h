// TESShout type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESShout.h.
// Layout of the bases between TESForm and the variations is not claimed. Adapted bodies: none declared.
// TESShout, TESShout::Variation, ::variations, ::GetKnown, Variation::word, ::spell, ::recoveryTime, ::pad14: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESWordOfPower: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the TESForm base is needed
// SpellItem: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); forward declaration
// TESShout::unk20: GUESS(low); stands for the bases from 0x20 to 0x5F
#pragma once

#include <cstdint>

#include "TESForm.h"

class SpellItem;

class TESWordOfPower : public TESForm {
};

class TESShout : public TESForm {
public:
    struct Variation {
        TESWordOfPower* word;          // 00
        SpellItem*      spell;         // 08
        float           recoveryTime;  // 10
        std::uint32_t   pad14;         // 14
    };
    static_assert(sizeof(Variation) == 0x18, "layout");

    bool GetKnown() const override;  // 17

    std::uint8_t unk20[0x40];     // 20
    Variation    variations[3];   // 60
};
static_assert(sizeof(TESShout) == 0xA8, "layout");
