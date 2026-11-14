// MagicTarget declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magictarget
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// MagicTarget: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// MagicTarget::GetTargetStatsObject, MagicTarget::IsInvulnerable, MagicTarget::MagicTargetIsActor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class TESObjectREFR;

class MagicTarget
{
public:
    virtual TESObjectREFR* GetTargetStatsObject();  // compared: 0x17ee10
    virtual bool IsInvulnerable();  // compared: 0x17ee30
    virtual bool MagicTargetIsActor() const;  // compared: 0x17eea0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x10];  // 08
};
static_assert(sizeof(MagicTarget) == 0x18, "MagicTarget size");
