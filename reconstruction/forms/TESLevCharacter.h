// TESLevCharacter declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-teslevcharacter
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESLevCharacter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject, TESBoundAnimObject: STANDIN EXE_RTTI
// TESLevCharacter::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TestBit: GUESS(low)
// unknown20, unknown30, unknown58: GUESS(low); NG models the two sub-objects at 0x30 and 0x58 as bases, here they are byte regions passed by address
// InitLeveledListState, InitModelTextureSwapState, ResetOwnerState: GUESS(low); callees at 0x1e9d60, 0x1ed110 and 0x1e60b0, declared and bound by hint
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESLevCharacter;

// Callees of InitItemImpl; declared, not defined here.
void InitLeveledListState(void* a_list, TESLevCharacter* a_owner);
void InitModelTextureSwapState(void* a_swap, TESLevCharacter* a_owner);
void ResetOwnerState(TESLevCharacter* a_owner, bool a_flag);

// TestBit: GUESS(low); flag bit tested as a load, read through a by-value helper.
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

class TESObject : public TESForm
{
public:
};

class TESBoundObject : public TESObject
{
public:
};

class TESBoundAnimObject : public TESBoundObject
{
public:
};

class TESLevCharacter : public TESBoundAnimObject
{
public:
    virtual void InitItemImpl();  // compared: 0x2717b0

    std::uint8_t unknown20[0x10];  // 20
    std::uint8_t unknown30[0x28];  // 30
    std::uint8_t unknown58[0x18];  // 58
};
