// Projectile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s06-projectile-projectile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// Projectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectREFR: STANDIN EXE_RTTI
// Projectile::GetActorCause, Projectile::Set3D, Projectile::GetPowerSpeedMult, Projectile::IsPermanent, Projectile::GetGravity, Projectile::SetActorCause, Projectile::HasKeywordHelper, Projectile::Update3D: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// ActorCause, ActorCause::refCount: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); the count at +0x14 that SetActorCause increments
// NiAVObject, NiAVObject::Update: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's Update is a table entry (id 70251); the call is a direct member call
// NiUpdateData, NiUpdateData::deltaTime, NiUpdateData::unk04: GUESS(low); the two-field record Update3D builds on the stack, a float then a 32-bit value of 1
// BGSKeyword: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// KeywordChecker, KeywordChecker::HasKeyword: GUESS(low); the subobject at +0x40 of the holder, with the keyword test at vtable offset 0x20; slots 0x00 to 0x03 are placeholders
// KeywordHolder, KeywordHolder::checker: GUESS(low); the holder pointed to at +0x160
// ProjectileInfo, ProjectileInfo::flags80, ProjectileInfo::gravity84: GUESS(low); the record at +0x40, with the flag dword at +0x80 that GetGravity tests at bit 17 and the float at +0x84
// TESDataHandler::singleton, TESDataHandler::IsTemporaryFormID: taken from the shared TESForm.h, which labels them there (meh321/AddressLibraryDatabase@0379cb6, permission for the callee at RVA 0x1c3680)
// g_updateDelta: GUESS(low); the global float at RVA 0x219e5f0 that Update3D passes as the delta
// TESObjectREFR::vslot3B to vslot6F: GUESS(low); placeholder virtual slots so that Get3D sits at vtable offset 0x380
// TESObjectREFR::Get3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares it in TESObjectREFR; the virtual that Update3D calls at vtable offset 0x380 and reads a pointer from
// Projectile::cause120, Projectile::keywordHolder160, Projectile::speedMult190, Projectile::flags1D4, Projectile::info40: GUESS(low); the pointers and values at +0x120, +0x160, +0x190, +0x1D4 and +0x40
// Projectile::Set3DBase: GUESS(low); the callee at RVA 0x2ead30 that Set3D tail-calls with the object and the queue flag
// ReleaseActorCause: GUESS(low); the callee at RVA 0x441f30 that SetActorCause tail-calls with the previous cause
// TestBit: GUESS(low); bit-index helper for the flag test in GetGravity
#pragma once

#include <intrin.h>
#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class ActorCause
{
public:
    std::uint8_t          unk00[0x14];  // 00
    volatile long         refCount;     // 14
};

class NiAVObject;
class BGSKeyword;

struct NiUpdateData
{
    float         deltaTime;  // 00
    std::int32_t  unk04;      // 04
};

class NiAVObject
{
public:
    void Update(NiUpdateData& a_data);
};

class KeywordChecker
{
public:
    virtual ~KeywordChecker();  // 00
    virtual void unk08();       // 01
    virtual void unk10();       // 02
    virtual void unk18();       // 03
    virtual bool HasKeyword(const BGSKeyword* a_keyword);  // 04
};

class KeywordHolder
{
public:
    std::uint8_t   unk00[0x40];  // 00
    KeywordChecker checker;      // 40
};

class ProjectileInfo
{
public:
    std::uint8_t  unk00[0x80];  // 00
    std::uint32_t flags80;      // 80
    float         gravity84;    // 84
};

extern float g_updateDelta;

void ReleaseActorCause(ActorCause* a_cause);

inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

class TESObjectREFR : public TESForm
{
public:
    virtual void vslot3B();
    virtual void vslot3C();
    virtual void vslot3D();
    virtual void vslot3E();
    virtual void vslot3F();
    virtual void vslot40();
    virtual void vslot41();
    virtual void vslot42();
    virtual void vslot43();
    virtual void vslot44();
    virtual void vslot45();
    virtual void vslot46();
    virtual void vslot47();
    virtual void vslot48();
    virtual void vslot49();
    virtual void vslot4A();
    virtual void vslot4B();
    virtual void vslot4C();
    virtual void vslot4D();
    virtual void vslot4E();
    virtual void vslot4F();
    virtual void vslot50();
    virtual void vslot51();
    virtual void vslot52();
    virtual void vslot53();
    virtual void vslot54();
    virtual void vslot55();
    virtual void vslot56();
    virtual void vslot57();
    virtual void vslot58();
    virtual void vslot59();
    virtual void vslot5A();
    virtual void vslot5B();
    virtual void vslot5C();
    virtual void vslot5D();
    virtual void vslot5E();
    virtual void vslot5F();
    virtual void vslot60();
    virtual void vslot61();
    virtual void vslot62();
    virtual void vslot63();
    virtual void vslot64();
    virtual void vslot65();
    virtual void vslot66();
    virtual void vslot67();
    virtual void vslot68();
    virtual void vslot69();
    virtual void vslot6A();
    virtual void vslot6B();
    virtual void vslot6C();
    virtual void vslot6D();
    virtual void vslot6E();
    virtual void vslot6F();
    virtual NiAVObject* Get3D();  // slot 0x70
};

class Projectile : public TESObjectREFR
{
public:
    virtual std::uint8_t Slot184() const;
    virtual ActorCause* GetActorCause() const;  // compared: 0x7fc070
    virtual void Set3D(NiAVObject* a_object, bool a_queue3DTasks = true);  // compared: 0x7fa5b0
    float GetPowerSpeedMult() const;  // compared: 0x7fc000
    bool IsPermanent() const;  // compared: 0x7fc440
    float GetGravity();  // compared: 0x7fc640
    virtual void SetActorCause(ActorCause* a_cause);  // compared: 0x7fc040
    virtual bool HasKeywordHelper(const BGSKeyword* a_keyword) const;  // compared: 0x7fe2b0
    void Update3D();  // compared: 0x7faf50
    void Set3DBase(NiAVObject* a_object, bool a_queue3DTasks);

    std::uint8_t    unk20[0x20];        // 20
    ProjectileInfo* info40;             // 40
    std::uint8_t    unk48[0xD8];        // 48
    ActorCause*     cause120;           // 120
    std::uint8_t    unk128[0x38];       // 128
    KeywordHolder*  keywordHolder160;   // 160
    std::uint8_t    unk168[0x28];       // 168
    float           speedMult190;       // 190
    std::uint8_t    unk194[0x40];       // 194
    std::uint32_t   flags1D4;           // 1D4
};
