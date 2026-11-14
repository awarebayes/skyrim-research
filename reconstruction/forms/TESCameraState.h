// TESCameraState declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s26-bsintrusiverefcounted-tescamerastate
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// TESCameraState: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESCameraState::GetRotation, TESCameraState::GetTranslation: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

// NiPoint3, NiQuaternion: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiPoint3::x, ::y, ::z, NiQuaternion::w, ::x, ::y, ::z: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class BGSLoadFormBuffer;

class NiPoint3
{
public:
    float x;  // 00
    float y;  // 04
    float z;  // 08
};
static_assert(sizeof(NiPoint3) == 0xC, "NiPoint3 size");

class NiQuaternion
{
public:
    float w;  // 00
    float x;  // 04
    float y;  // 08
    float z;  // 0C
};
static_assert(sizeof(NiQuaternion) == 0x10, "NiQuaternion size");

// niPointZero: GUESS(low); the NiPoint3 global at RVA 0x331c458, bound by the unit's bind-hints.json
extern "C" NiPoint3 niPointZero;
// niQuatDefault: GUESS(low); the NiQuaternion global at RVA 0x331d790, bound by the unit's bind-hints.json
extern "C" NiQuaternion niQuatDefault;

class TESCameraState
{
public:
    virtual void GetRotation(NiQuaternion& a_rotation);  // compared: 0x24a020
    virtual void GetTranslation(NiPoint3& a_translation);  // compared: 0x24a030
    // TESCameraState::Begin, TESCameraState::End, TESCameraState::LoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x24a000, 0x24a010, 0x24a060
    virtual void Begin();  // compared: 0x24a000
    virtual void End();  // compared: 0x24a010
    virtual void LoadGame(BGSLoadFormBuffer* a_buf);  // compared: 0x24a060

    std::uint8_t unknown08[0x18];  // 08
};
static_assert(sizeof(TESCameraState) == 0x20, "TESCameraState size");
