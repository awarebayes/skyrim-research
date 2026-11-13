// BSXAudio2AudioListener declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s22-bsaudiolistener-bsxaudio2audiolistener
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSAudioListener.h for BSAudioListener.
// BSXAudio2AudioListener: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSXAudio2AudioListener::Unk_01: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// BSXAudio2AudioListener::Unk_06: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); the parameter is read from the listing (a pointer to three dwords)
// field58, field60, field64, field68, field6C, unknown40, unknown70: GUESS(low)
#pragma once

#include <cstdint>
#include "../bsengine/BSAudioListener.h"

class BSXAudio2AudioListener : public BSAudioListener
{
public:
    virtual void Unk_01();  // compared: 0xcd8c80
    virtual void Unk_06(const std::uint32_t* a_src);  // compared: 0xcd8da0

    std::uint8_t unknown40[0x18];  // 40
    std::uint64_t field58;  // 58
    std::uint32_t field60;  // 60
    std::uint32_t field64;  // 64
    std::uint32_t field68;  // 68
    std::uint32_t field6C;  // 6C
    std::uint8_t unknown70[0x8];  // 70
};
static_assert(sizeof(BSXAudio2AudioListener) == 0x78, "BSXAudio2AudioListener size");
