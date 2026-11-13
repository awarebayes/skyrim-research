// BeamProjectile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s06-projectile-beamprojectile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSSaveFormBuffer.h for BGSSaveFormBuffer and TESForm.
// BGSSaveFormBuffer.h also declares TESObjectREFR, so the TESObjectREFR.h shared header is not included.
// BeamProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Projectile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); pads the base to 0x240, the offset of the member the compared code writes
// BeamProjectile::Revert, BeamProjectile::SaveGame: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Projectile::Revert, Projectile::SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); called non-virtually by the compared code
// BGSSaveGameBuffer::SaveDataEndian: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); name only, four target arguments are declared in its shared header
// unk240: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/BGSSaveFormBuffer.h"

class BGSLoadFormBuffer;

class Projectile : public TESObjectREFR
{
public:
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared base call: 0x7fbcf0
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared base call: 0x7fb000

    std::uint8_t unkBase[0x240 - sizeof(TESObjectREFR)];  // pads to the member at 0x240
};

class BeamProjectile : public Projectile
{
public:
    virtual std::uint8_t Slot165() const;
    virtual void Revert(BGSLoadFormBuffer* a_buf);  // compared: 0x7e03e0
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared: 0x7e0320

    std::uint8_t unk240;  // 240
};
