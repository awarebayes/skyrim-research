// BGSLightingTemplate type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSLightingTemplate, BGSLightingTemplate::InitializeData, ::data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// INTERIOR_DATA: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); size 0x60, only fogClamp is named, the rest is opaque bytes
// INTERIOR_DATA::fogClamp: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); offset 0x4C
// INTERIOR_DATA::unk00, ::unk50: GUESS(low); opaque bytes standing for the other members
// BGSDirectionalAmbientLightingColors: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, 0x20 bytes at offset 0x80
// BGSDirectionalAmbientLightingColors::unk00: GUESS(low); opaque bytes
#pragma once

#include <cstdint>

#include "TESForm.h"

struct INTERIOR_DATA {
    std::uint8_t unk00[0x4C];  // 00
    float        fogClamp;     // 4C
    std::uint8_t unk50[0x10];  // 50
};
static_assert(sizeof(INTERIOR_DATA) == 0x60, "layout");

struct BGSDirectionalAmbientLightingColors {
    std::uint8_t unk00[0x20];  // 00
};

class BGSLightingTemplate : public TESForm {
public:
    void InitializeData() override;  // 04

    INTERIOR_DATA                       data;                              // 20
    BGSDirectionalAmbientLightingColors directionalAmbientLightingColors;  // 80
};
