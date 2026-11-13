// BGSSceneActionTimer declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneactiontimer
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSSceneAction.h for BGSSceneAction.
// BGSSceneActionTimer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSSceneActionTimer::Unk_0D, BGSSceneActionTimer::~BGSSceneActionTimer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown20: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/BGSSceneAction.h"

class BGSSceneActionTimer
{
public:
    BGSSceneActionTimer();
    virtual void Unk_0D();  // compared: 0x3ad170
    virtual ~BGSSceneActionTimer();  // compared: 0x3ad400 (scalar deleting destructor)
    // Unk_0DTarget: GUESS(low)
    void Unk_0DTarget();

    std::uint8_t unknown08[0x1c];  // 08
    // unknown24: GUESS(low)
    volatile std::uint32_t unknown24;  // 24
    // unknown28: GUESS(low)
    volatile std::uint16_t unknown28;  // 28
    std::uint8_t unknown2A[0x6];  // 2A
};
static_assert(sizeof(BGSSceneActionTimer) == 0x30, "BGSSceneActionTimer size");
