// MissileProjectile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s06-projectile-missileprojectile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// MissileProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectREFR, Projectile: STANDIN EXE_RTTI
// MissileProjectile::GetKillOnCollision, MissileProjectile::LoadGame, MissileProjectile::FinishLoadGame, MissileProjectile::SaveGame: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// ImpactResult, ImpactResult::kNone, ImpactResult::kDestroy: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MissileProjectile::impactResult: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); powerof3 places it at 0x1D8 in SE, this build's listing reads it at 0x1E0
// MissileProjectile::unk1E4: GUESS(low); the byte the load path sets to 1 when no saved state is found
// MissileProjectile::unk20: GUESS(low)
// MissileProjectile::PrepareSave, MissileProjectile::PrepareLoad, MissileProjectile::PrepareFinishLoad, MissileProjectile::ContinueFinishLoad: GUESS(low); members called with this before or after the buffer work, the callees at RVA 0x7fb000, 0x7fb3b0, 0x7fbb70 and 0x7f4e80
// TESObjectREFR::unk3B to unk70: GUESS(low); placeholder virtual slots so that unk70 sits at vtable offset 0x380; the listing calls it through that offset and takes only this
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class TESObjectREFR : public TESForm
{
public:
    virtual void unk3B();
    virtual void unk3C();
    virtual void unk3D();
    virtual void unk3E();
    virtual void unk3F();
    virtual void unk40();
    virtual void unk41();
    virtual void unk42();
    virtual void unk43();
    virtual void unk44();
    virtual void unk45();
    virtual void unk46();
    virtual void unk47();
    virtual void unk48();
    virtual void unk49();
    virtual void unk4A();
    virtual void unk4B();
    virtual void unk4C();
    virtual void unk4D();
    virtual void unk4E();
    virtual void unk4F();
    virtual void unk50();
    virtual void unk51();
    virtual void unk52();
    virtual void unk53();
    virtual void unk54();
    virtual void unk55();
    virtual void unk56();
    virtual void unk57();
    virtual void unk58();
    virtual void unk59();
    virtual void unk5A();
    virtual void unk5B();
    virtual void unk5C();
    virtual void unk5D();
    virtual void unk5E();
    virtual void unk5F();
    virtual void unk60();
    virtual void unk61();
    virtual void unk62();
    virtual void unk63();
    virtual void unk64();
    virtual void unk65();
    virtual void unk66();
    virtual void unk67();
    virtual void unk68();
    virtual void unk69();
    virtual void unk6A();
    virtual void unk6B();
    virtual void unk6C();
    virtual void unk6D();
    virtual void unk6E();
    virtual void unk6F();
    virtual void* unk70();  // slot 0x70
};

class Projectile : public TESObjectREFR
{
public:
};

enum class ImpactResult : std::int32_t
{
    kNone    = 0,
    kDestroy = 1
};

class MissileProjectile : public Projectile
{
public:
    virtual std::uint8_t Slot162() const;
    virtual bool GetKillOnCollision();  // compared: 0x7f4d40
    virtual void LoadGame(BGSLoadFormBuffer* a_buf);  // compared: 0x7f4dc0
    virtual void FinishLoadGame(BGSLoadFormBuffer* a_buf);  // compared: 0x7f4e10
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared: 0x7f4d70

    void PrepareSave();
    void PrepareLoad();
    void PrepareFinishLoad();
    void ContinueFinishLoad();

    std::uint8_t unk20[0x1C0];    // 20
    ImpactResult impactResult;    // 1E0
    std::uint8_t unk1E4;          // 1E4
};
