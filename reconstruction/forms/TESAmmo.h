// TESAmmo declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-tesammo
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESAmmo: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject: STANDIN EXE_RTTI
// TESAmmo::GetPlayable, TESAmmo::InitializeData, TESAmmo::SaveGame: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

// ammoDefault: GUESS(low); the float global at RVA 0x207a998, bound by the unit's bind-hints.json
extern "C" float ammoDefault;
// InitializeSubobject, SaveSubobject: GUESS(low); the callees at RVAs 0x20d150 and 0x1f3660
void InitializeSubobject(void* a_obj, bool a_flag);
void SaveSubobject(void* a_obj, BGSSaveFormBuffer* a_buf);
// TestBit: GUESS(low)
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit) { return ((a_flags >> a_bit) & 1) != 0; }

class TESObject : public TESForm
{
public:
};

class TESBoundObject : public TESObject
{
public:
};

class TESAmmo : public TESBoundObject
{
public:
    virtual bool GetPlayable() const;  // compared: 0x2695f0
    virtual void InitializeData();  // compared: 0x268ac0
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared: 0x2692c0

    // unknown20, unkA0, unkBC, unk110, unk118, unk120: GUESS(low)
    std::uint8_t  unknown20[0x80];  // 20
    std::uint8_t  unkA0[0x18];      // A0
    float         unkB8;            // B8
    std::uint8_t  unkBC[0x54];      // BC
    std::uint64_t unk110;           // 110
    std::uint8_t  unk118[0x8];      // 118
    std::uint8_t  unk120[0x8];      // 120
};
