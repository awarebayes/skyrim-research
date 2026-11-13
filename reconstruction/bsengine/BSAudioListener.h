// BSAudioListener declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s22-bsaudiolistener-bsaudiolistener
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSAudioListener: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSAudioListener::Unk_05: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown08, unk2C, unk34: GUESS(low)
// unk30, unk38: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
#pragma once

#include <cstdint>

class BSAudioListener
{
public:
    virtual void Unk_05(const std::uint32_t* a_src);  // compared: 0xcd69f0

    std::uint8_t  unknown08[0x24];  // 08
    std::uint32_t unk2C;            // 2C
    std::uint32_t unk30;            // 30
    std::uint32_t unk34;            // 34
    std::uint8_t  unk38[0x8];       // 38
};
static_assert(sizeof(BSAudioListener) == 0x40, "BSAudioListener size");
