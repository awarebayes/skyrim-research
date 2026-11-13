// BGSLoadFormBuffer declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s01-bgsloadgamebuffer-bgsloadformbuffer
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSLoadGameBuffer.h for BGSLoadGameBuffer.
// BGSLoadFormBuffer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSLoadFormBuffer::GetVersion: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown28: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/BGSLoadGameBuffer.h"

class BGSLoadFormBuffer : public BGSLoadGameBuffer
{
public:
    virtual std::uint8_t GetVersion();  // compared: 0x637580

    std::uint8_t unknown28[0x23];  // 28
    // version: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint8_t version;  // 4b
    std::uint8_t unknown4c[0x4];  // 4c
};
static_assert(sizeof(BGSLoadFormBuffer) == 0x50, "BGSLoadFormBuffer size");
