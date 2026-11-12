// Type declarations for the MagicCaster unit (build sse-steam-1-7-104).
// Labels: v2
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT);
// AIFormulas::GetSoundLevelValue follows powerof3/CommonLibSSE 654e55f7979c1733033d5dbef176e43827bac944
// (GPL-3.0, used as a naming source per docs/authorizations.md).
// Adapted code: the inline body of BSTArray::operator[] is adapted from CharmedBaryon/CommonLibSSE-NG
// b93280e include/RE/B/BSTArray.h under its MIT licence (its assert dropped, the data member
// indexed directly instead of through data()).
// Bodies adapted from community sources are listed above; tools/check_origin.py reports none
// other above its threshold (0.75) at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f
// and momusdigital/fnv_decomp 91e1b6e8. NG's licence notice, from its LICENSE at
// b93280e, is kept as it requires:
//
//   MIT License
//
//   Copyright (c) 2018 Ryan-rsm-McKenzie
//
//   Permission is hereby granted, free of charge, to any person obtaining a copy
//   of this software and associated documentation files (the "Software"), to deal
//   in the Software without restriction, including without limitation the rights
//   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//   copies of the Software, and to permit persons to whom the Software is
//   furnished to do so, subject to the following conditions:
//
//   The above copyright notice and this permission notice shall be included in all
//   copies or substantial portions of the Software.
//
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//   SOFTWARE.
//
// All declarations are minimal stand-ins that carry only the members and virtual slots the
// compared functions use; their layouts are not claimed to match the game beyond the offsets given.
// MagicCaster: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicCaster::sounds MagicCaster::currentSpell MagicCaster::state MagicCaster::currentSpellCost: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); at 0x08, 0x28, 0x30, 0x38
// MagicCaster::State MagicCaster::State::kUnk09: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicCaster::InterruptCastImpl MagicCaster::SpellCast MagicCaster::GetCasterAsActor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); virtual slots 0x08, 0x09, 0x0c
// MagicCaster::GetCurrentSpellCost MagicCaster::InterruptCast MagicCaster::FindPickTarget MagicCaster::PlayReleaseSound MagicCaster::FinishCast: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicCaster::ContinueFindPickTarget: GUESS(low); callee at RVA 0x5cefc0 has no community name; bound by hint.
// MagicCaster unkNN virtuals: GUESS; filler slots so the used virtuals land on their NG slots.
// BSTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); data pointer, capacity and size only, as BSTArrayHeapAllocator and BSTArrayBase lay them out
// BSSoundHandle BSSoundHandle::soundID BSSoundHandle::Stop: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicSystem MagicSystem::SoundID MagicSystem::SoundID::kCharge MagicSystem::SoundID::kReadyLoop MagicSystem::SoundID::kCastLoop: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); values 1, 2, 4
// MagicSystem::Delivery MagicSystem::Delivery::kTargetActor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicItem: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicItem::GetDelivery MagicItem::GetRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); virtual slots 0x57 and 0x5a
// MagicItem::CalculateCost MagicItem::GetAVEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicItem unkNN virtuals: GUESS; filler slots so GetDelivery/GetRange land on slots 0x57 and 0x5a.
// EffectSetting EffectSetting::EffectSettingData EffectSetting::data EffectSettingData::castingSoundLevel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); data at 0x68, castingSoundLevel at 0xe0 of it
// SOUND_LEVEL: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESObjectREFR TESObjectREFR::data OBJ_REFR OBJ_REFR::location: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); data at 0x40, location at 0x14 of it
// Actor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Actor::currentProcess: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); at 0xf8 (NG's SE offset 0xf0 plus 8)
// AIProcess: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// AIProcess::SetActorsDetectionEvent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicTarget NiPoint3 TESObjectCELL bhkPickData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSEntryPoint BGSEntryPoint::HandleEntryPoint BGSEntryPoint::ENTRY_POINTS BGSEntryPoint::ENTRY_POINTS::ENTRY_POINT: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ENTRY_POINT::kModSpellCastingSoundEvent ENTRY_POINT::kModSpellRange_TargetLoc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); values 55 and 88
// AIFormulas AIFormulas::GetSoundLevelValue: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// ApplySoundEvent: GUESS(low); callee at RVA 0x69fe50 has no community name; bound by hint.
#pragma once

#include <cstdint>

class TESObjectCELL;
class bhkPickData;
class MagicTarget;

class NiPoint3 {
public:
    float x;
    float y;
    float z;
};

template <class T>
class BSTArray {
public:
    T& operator[](std::uint32_t a_pos) { return data[a_pos]; }

    T*            data;      // 0x00
    std::uint32_t capacity;  // 0x08
    std::uint32_t pad0C;     // 0x0c
    std::uint32_t size;      // 0x10
    std::uint32_t pad14;     // 0x14
};

class BSSoundHandle {
public:
    bool Stop();

    std::uint32_t soundID;  // 0x00
    std::uint8_t  unk04[8];
};

namespace MagicSystem {
    enum class SoundID {
        kCharge    = 1,
        kReadyLoop = 2,
        kCastLoop  = 4,
    };

    enum class Delivery {
        kTargetActor = 3,
    };
}

enum class SOUND_LEVEL {
};

struct OBJ_REFR {
    std::uint8_t unk00[0x14];
    NiPoint3     location;  // 0x14
};

class TESObjectREFR {
public:
    std::uint8_t unk00[0x40];
    OBJ_REFR     data;  // 0x40
};

class Actor;

class AIProcess {
public:
    void SetActorsDetectionEvent(Actor* a_actor, const NiPoint3& a_location, std::int32_t a_soundLevel, TESObjectREFR* a_ref);
};

class Actor : public TESObjectREFR {
public:
    std::uint8_t unk60[0xf8 - 0x60];
    AIProcess*   currentProcess;  // 0xf8
};

class EffectSetting {
public:
    struct EffectSettingData {
        std::uint8_t unk00[0xe0];
        SOUND_LEVEL  castingSoundLevel;  // 0xe0
    };

    std::uint8_t      unk00[0x68];
    EffectSettingData data;  // 0x68
};

class MagicItem {
public:
    virtual ~MagicItem();
    virtual void unk00();
    virtual void unk01();
    virtual void unk02();
    virtual void unk03();
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void unk07();
    virtual void unk08();
    virtual void unk09();
    virtual void unk0a();
    virtual void unk0b();
    virtual void unk0c();
    virtual void unk0d();
    virtual void unk0e();
    virtual void unk0f();
    virtual void unk10();
    virtual void unk11();
    virtual void unk12();
    virtual void unk13();
    virtual void unk14();
    virtual void unk15();
    virtual void unk16();
    virtual void unk17();
    virtual void unk18();
    virtual void unk19();
    virtual void unk1a();
    virtual void unk1b();
    virtual void unk1c();
    virtual void unk1d();
    virtual void unk1e();
    virtual void unk1f();
    virtual void unk20();
    virtual void unk21();
    virtual void unk22();
    virtual void unk23();
    virtual void unk24();
    virtual void unk25();
    virtual void unk26();
    virtual void unk27();
    virtual void unk28();
    virtual void unk29();
    virtual void unk2a();
    virtual void unk2b();
    virtual void unk2c();
    virtual void unk2d();
    virtual void unk2e();
    virtual void unk2f();
    virtual void unk30();
    virtual void unk31();
    virtual void unk32();
    virtual void unk33();
    virtual void unk34();
    virtual void unk35();
    virtual void unk36();
    virtual void unk37();
    virtual void unk38();
    virtual void unk39();
    virtual void unk3a();
    virtual void unk3b();
    virtual void unk3c();
    virtual void unk3d();
    virtual void unk3e();
    virtual void unk3f();
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
    virtual void unk4a();
    virtual void unk4b();
    virtual void unk4c();
    virtual void unk4d();
    virtual void unk4e();
    virtual void unk4f();
    virtual void unk50();
    virtual void unk51();
    virtual void unk52();
    virtual void unk53();
    virtual void unk54();
    virtual void unk55();
    virtual MagicSystem::Delivery GetDelivery() const;  // 57
    virtual void                  unk58();
    virtual void                  unk59();
    virtual float                 GetRange() const;  // 5A

    float          CalculateCost(Actor* a_caster) const;
    EffectSetting* GetAVEffect() const;
};

struct BGSEntryPoint {
    struct ENTRY_POINTS {
        enum ENTRY_POINT : std::uint32_t {
            kModSpellCastingSoundEvent = 55,
            kModSpellRange_TargetLoc   = 88,
        };
    };
    using ENTRY_POINT = ENTRY_POINTS::ENTRY_POINT;

    template <class... Args>
    static void HandleEntryPoint(ENTRY_POINT a_entryPoint, Actor* a_perkOwner, Args... a_args);
};

namespace AIFormulas {
    std::int32_t GetSoundLevelValue(SOUND_LEVEL a_soundLevel);
}

void ApplySoundEvent(Actor* a_actor, std::int32_t a_soundLevel);

class MagicCaster {
public:
    enum class State : std::uint32_t {
        kUnk09 = 9
    };

    virtual ~MagicCaster();
    virtual void   unk01();
    virtual void   unk02();
    virtual void   unk03();
    virtual void   unk04();
    virtual void   unk05();
    virtual void   unk06();
    virtual void   unk07();
    virtual void   InterruptCastImpl(bool a_depleteEnergy);                              // 08
    virtual void   SpellCast(bool a_doCast, std::uint32_t a_arg2, MagicItem* a_spell);  // 09
    virtual void   unk0a();
    virtual void   unk0b();
    virtual Actor* GetCasterAsActor() const;  // 0C

    float        GetCurrentSpellCost();
    void         InterruptCast(bool a_refund);
    MagicTarget* FindPickTarget(NiPoint3& a_targetLocation, TESObjectCELL** a_targetCell, bhkPickData& a_pickData);
    void         PlayReleaseSound(MagicItem* a_item);
    void         FinishCast();
    MagicTarget* ContinueFindPickTarget(bool a_hostile, float a_range, NiPoint3& a_targetLocation, TESObjectCELL** a_targetCell, bhkPickData& a_pickData);

    BSTArray<BSSoundHandle> sounds;            // 0x08
    std::uint8_t            unk20[0x08];       // 0x20
    MagicItem*              currentSpell;      // 0x28
    State                   state;             // 0x30
    std::uint32_t           unk34;             // 0x34
    float                   currentSpellCost;  // 0x38
};
