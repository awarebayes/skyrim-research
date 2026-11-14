// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (community headers and pinned-image analysis).
// Drafted by gpt-6.1-sol, Engineer p105 box3. Adapted bodies: none.
// Declarations adapt CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a (MIT).
// Helper spellings and local variable names are inferred; individual labels accompany declarations.
// MIT License
// 
// Copyright (c) 2018 Ryan-rsm-McKenzie
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// FlameProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
#include "TESForm.h"
// The following bases and members represent the AE object rather than allocation-size storage.
// NiRefObject, BSHandleRefObject, BSTEventSink, IAnimationGraphManagerHolder, NiPoint3, NiTransform, OBJ_REFR, BaseExtraList, ReferenceExtraDataList, TESObjectREFR, Projectile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRefObject { public: virtual ~NiRefObject(); virtual void DeleteThis(); volatile std::uint32_t refCount; };
class BSHandleRefObject : public NiRefObject { public: ~BSHandleRefObject() override; };
class BSAnimationGraphEvent;
template<class T> class BSTEventSink { public: virtual ~BSTEventSink(); virtual void ProcessEvent(); };
class IAnimationGraphManagerHolder { public: virtual ~IAnimationGraphManagerHolder(); virtual void Unk01(); };
struct NiPoint3 { float x,y,z; };
struct NiTransform { float rotate[3][3]; NiPoint3 translate; float scale; };
struct OBJ_REFR { TESBoundObject* objectReference; NiPoint3 angle,location; };
class BSExtraData;
class BaseExtraList { public: virtual ~BaseExtraList(); BSExtraData* data; void* presence; };
struct ReferenceExtraDataList { BaseExtraList data; std::uint32_t threadID,lock; };
class TESObjectREFR : public TESForm, public BSHandleRefObject, public BSTEventSink<BSAnimationGraphEvent>, public IAnimationGraphManagerHolder {
public:
 virtual ~TESObjectREFR();
 OBJ_REFR data; void* parentCell; void* loadedData; ReferenceExtraDataList extraList;
 std::uint64_t unk90; std::uint16_t refScale; std::int8_t modelState; bool preDestroyed;
};
static_assert(sizeof(TESObjectREFR)==0xA0,"AE reference size");
struct ProjectileImpactList { void* item; void* next; };
struct ProjectileSoundHandle { std::uint32_t soundID; bool assumeSuccess; std::uint8_t state; std::uint16_t unknown6; std::uint32_t unknown8; };
class Projectile : public TESObjectREFR {
public:
 Projectile();
 void LoadGame(BGSLoadFormBuffer*); void SaveGame(BGSSaveFormBuffer*);
 ProjectileImpactList impacts;
 NiTransform transform; float unkE4; void* shapePhantom; std::uint32_t lockThread,lockCount;
 NiPoint3 velocity,linearVelocity;
 void* light; void* unk118; void* actorCause;
 std::uint32_t shooter,desiredTarget;
 ProjectileSoundHandle sound,countdown;
 std::uint32_t* unk148; void* inventoryEntry; void* explosion; void* spell;
 std::uint32_t castingSource; void* avEffect; void* queuedFiles;
 std::uint64_t unk180,unk188;
 float power,speedMult,range,livingTime,weaponDamage,transparency,explosionTimer;
 std::uint32_t unk1AC; float unk1B0,unk1B4; void* weaponSource; void* ammoSource;
 float distanceMoved; std::uint32_t unk1CC; float scale; std::uint32_t flags;
 bool unk1D8,unk1D9;
};
static_assert(sizeof(Projectile)==0x1E0,"AE projectile size");
class FlameProjectile : public Projectile {
public:
 FlameProjectile(); virtual ~FlameProjectile(); virtual std::uint8_t Slot164() const;
 void LoadGame(BGSLoadFormBuffer*); void SaveGame(BGSSaveFormBuffer*);
 union { void* runtimeTimers; struct { std::uint32_t expirationTimer,coneAngle; } timers; };
};
static_assert(sizeof(FlameProjectile)==0x1E8,"AE flame projectile size");
void BGSLoadGameBuffer_LoadDataEndian(BGSLoadFormBuffer*,void*,std::uint32_t,std::uint32_t);
void BGSSaveGameBuffer_SaveDataEndian(BGSSaveFormBuffer*,void*,std::uint32_t,std::uint32_t,std::uint32_t);

