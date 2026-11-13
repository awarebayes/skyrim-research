// Explosion declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s04-tesobjectrefr-explosion
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// Explosion: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectREFR: STANDIN EXE_RTTI
// Explosion::GetMagicCaster, Explosion::FinishLoadGame, Explosion::SetActorCause, Explosion::~Explosion: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Explosion::FinishLoadGame: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); the listing takes no argument beyond this, so the declaration drops the buffer parameter
// MagicSystem::CastingSource: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicCaster: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); only its address is taken
// ExplosionCasterHolder, ExplosionCasterHolder::caster: GUESS(low); the object at the pointer stored at +0x110, with the caster at +0x10
// ActorCause: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// ActorCause::refCount: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); the 32-bit count at +0x14 that SetActorCause increments
// ExplosionManager: STANDIN GUESS(low); only the pointer is used
// g_explosionManager: GUESS(low); the global pointer at RVA 0x3211948 that FinishLoadGame passes on
// ReleaseActorCause: GUESS(low); the callee at RVA 0x441f30 takes the previous cause and releases its reference
// AddExplosionToManager: GUESS(low); the callee at RVA 0x7e3610 takes the manager and the explosion
// Explosion::PrepareLoadState: GUESS(low); the callee at RVA 0x2e1180 is called with this before the manager call
// Explosion::unk20, Explosion::cause108, Explosion::holder110: GUESS(low); cause108 is the ActorCause pointer at +0x108, holder110 the caster holder at +0x110
// Explosion::unk118: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares a 32-bit field here, this unit keeps the bytes as padding
#pragma once

#include <intrin.h>
#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class Explosion;

class MagicCaster
{
public:
    std::uint8_t unk00[0x8];  // 00
};

class ExplosionCasterHolder
{
public:
    std::uint8_t unk00[0x10];  // 00
    MagicCaster  caster;       // 10
};

class ActorCause
{
public:
    std::uint8_t             unk00[0x14];  // 00
    volatile long            refCount;     // 14
};

class ExplosionManager;

extern ExplosionManager* g_explosionManager;

void ReleaseActorCause(ActorCause* a_cause);
void AddExplosionToManager(ExplosionManager* a_manager, Explosion* a_explosion);

namespace MagicSystem { enum class CastingSource : int; }

class TESObjectREFR : public TESForm
{
public:
};

class Explosion : public TESObjectREFR
{
public:
    virtual void* GetActorCause() const;
    Explosion();
    virtual MagicCaster* GetMagicCaster(MagicSystem::CastingSource a_source);  // compared: 0x7e8b50
    virtual void FinishLoadGame();  // compared: 0x7e5720
    virtual void SetActorCause(ActorCause* a_cause);  // compared: 0x64cea0
    virtual ~Explosion();  // compared: 0x7e9ca0 (scalar deleting destructor); declared only, the complete destructor is a separate call
    void PrepareLoadState();

    std::uint8_t           unk20[0xE8];       // 20
    ActorCause*            cause108;          // 108
    ExplosionCasterHolder* holder110;         // 110
    std::uint8_t           unk118[0x30];      // 118
};
static_assert(sizeof(Explosion) == 0x148, "Explosion size");
