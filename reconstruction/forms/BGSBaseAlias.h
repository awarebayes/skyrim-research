// BGSBaseAlias declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsbasealias
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSBaseAlias::~BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

// AliasMemberCleanupStub: GUESS(low); releases the member block at 0x8 (0xeb1100)
void AliasMemberCleanupStub(void* a_member) noexcept;

class BGSBaseAlias
{
public:
    BGSBaseAlias();
    virtual ~BGSBaseAlias();  // compared: 0x392c60 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x20];  // 08
};
static_assert(sizeof(BGSBaseAlias) == 0x28, "BGSBaseAlias size");
