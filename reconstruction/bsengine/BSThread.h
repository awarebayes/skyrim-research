// BSThread declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsthread
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSThread: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSThread::Unk_02, BSThread::Unk_01: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
// Signature change from the community list: Unk_01 returns std::uint32_t, because the compared code returns 0 in EAX
#pragma once

#include <cstdint>
#include <cstddef>

class BSThread
{
public:
    virtual void Unk_02();  // compared: 0x60f1d0
    virtual std::uint32_t Unk_01();  // compared: 0xceb190

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x48];  // 08
};
static_assert(sizeof(BSThread) == 0x50, "BSThread size");
