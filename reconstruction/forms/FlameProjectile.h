// FlameProjectile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s06-projectile-flameprojectile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESObjectREFR.h for TESObjectREFR and TESForm. It defines TESForm
// itself, so ../forms/TESForm.h is not included here (the two shared headers cannot be combined).
// FlameProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Projectile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); pads the base to the flags word at 0x1D4
// FlameProjectile::Handle3DLoaded, FlameProjectile::Revert, FlameProjectile::~FlameProjectile: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Projectile::Revert: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); called non-virtually by the compared code
// Projectile::flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares flags at 0x1CC, this build uses 0x1D4
// FlameProjectile size 0x1E8: OBSERVED; the compared deleting destructor passes it to operator delete
// unk1E0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESObjectREFR.h"

class BGSLoadFormBuffer;

class Projectile : public TESObjectREFR
{
public:
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared base call: 0x7fbcf0

    std::uint8_t unkBase[0x1D4 - sizeof(TESObjectREFR)];  // pads to flags
    std::uint32_t flags;  // 1D4
};

class FlameProjectile : public Projectile
{
public:
    virtual std::uint8_t Slot164() const;
    FlameProjectile();
    virtual void Handle3DLoaded();  // compared: 0x7eb430
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared: 0x7eb240
    virtual ~FlameProjectile();  // compared: 0x7eb510 (scalar deleting destructor)

    std::uint8_t  unk1D8[0x8];  // 1D8
    std::uint64_t unk1E0;       // 1E0
};
static_assert(sizeof(FlameProjectile) == 0x1E8, "FlameProjectile size");
