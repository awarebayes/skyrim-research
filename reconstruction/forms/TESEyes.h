// TESEyes type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESEyes.h.
// The layout of the members beyond TESForm is not claimed; the bases at 0x20 and 0x30 are
// represented by an opaque block so that the flags byte sits at 0x40.
// Adapted bodies: none declared.
// TESEyes, TESEyes::InitializeData, TESEyes::flags, TESEyes::pad41: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

#include "TESForm.h"

// TESEyes: EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESEyes : public TESForm {
public:
    // TESEyes::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    void InitializeData() override;  // 04

    // unk20: GUESS(low); stands for the TESFullName and TESTexture bases (0x20 to 0x3F), not claimed
    std::uint8_t unk20[0x20];  // 20
    // flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares an enumeration over uint8
    std::uint8_t flags;  // 40
    // pad41: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint8_t pad41[7];  // 41
};
static_assert(sizeof(TESEyes) == 0x48, "layout");
