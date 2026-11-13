// BarrierProjectile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s06-projectile-barrierprojectile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BarrierProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectREFR, Projectile: STANDIN EXE_RTTI
// BarrierProjectile::UpdateImpl, BarrierProjectile::Revert: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// TESObjectREFR::objectReference: GUESS(low); NG names it data.objectReference, the first member of its OBJ_REFR at 0x40
// TESBoundObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the float at 0xF0 is used, the rest is padding
// Projectile::Kill: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); non-virtual, the compared code tail-jumps to it
// Projectile::Revert: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the compared code calls it non-virtually
// Projectile::transparency: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's runtime data at 0x19C
// unkF0, unk20, pad48, unk1A0, unk1E0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class TESObjectREFR : public TESForm
{
public:
    std::uint8_t unk20[0x20];  // 20
    class TESBoundObject* objectReference;  // 40
};

class TESBoundObject : public TESForm
{
public:
    std::uint8_t unk20[0xD0];  // 20
    float        unkF0;        // F0
};

class Projectile : public TESObjectREFR
{
public:
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared base call: 0x7fbcf0
    void Kill();  // tail jump target: 0x7f9d70

    std::uint8_t pad48[0x154];  // 48
    float        transparency;  // 19C
};

class BarrierProjectile : public Projectile
{
public:
    virtual std::uint8_t Slot167() const;
    virtual void UpdateImpl(float a_delta);  // compared: 0x7df690
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared: 0x7df760

    std::uint8_t  unk1A0[0x40];  // 1A0
    std::uint32_t unk1E0;        // 1E0
};
