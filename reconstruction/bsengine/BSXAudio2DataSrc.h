// BSXAudio2DataSrc declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsxaudio2datasrc
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSXAudio2DataSrc: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSAudioDataSrc_VBSXAudio2DataSrc: STANDIN EXE_RTTI
// BSXAudio2DataSrc::~BSXAudio2DataSrc: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// BSAudioDataSrc_VBSXAudio2DataSrc::~BSAudioDataSrc_VBSXAudio2DataSrc, unknown08, unknown18: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSAudioDataSrc_VBSXAudio2DataSrc
{
public:
    virtual ~BSAudioDataSrc_VBSXAudio2DataSrc() = default;
    std::uint8_t unknown08[0x10];  // 08
};
static_assert(sizeof(BSAudioDataSrc_VBSXAudio2DataSrc) == 0x18, "BSAudioDataSrc_VBSXAudio2DataSrc size");

class BSXAudio2DataSrc : public BSAudioDataSrc_VBSXAudio2DataSrc
{
public:
    BSXAudio2DataSrc();
    virtual ~BSXAudio2DataSrc();  // compared: 0xcdc8e0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown18[0xA8];  // 18
};
static_assert(sizeof(BSXAudio2DataSrc) == 0xC0, "BSXAudio2DataSrc size");
