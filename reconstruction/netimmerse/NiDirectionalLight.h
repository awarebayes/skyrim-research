// NiDirectionalLight declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nidirectionallight
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: NiLightBase, a local stand-in of the NiLight 0x140 size. The shared NiAVObject cannot
// hold the fields at 0x7C to 0x94 that the compared code reads, so they are declared here.
// NiDirectionalLight: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// NiDirectionalLight::~NiDirectionalLight, NiDirectionalLight::UpdateWorldData, NiDirectionalLight::GetRTTI: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// NiLightBase, lightA, lightB, lightC, unk08, unk80, unk8C, unk98, copyA, copyB, copyC, unk14C: GUESS(low); names and layout inferred from the listings
// BaseUpdateWorldData, the NiLightBase destructor, NiRTTI_NiDirectionalLight: GUESS(low); bound by address through bind-hints.json
#pragma once

#include <cstdint>
#include <cstddef>

class NiRTTI;

// NiRTTI_NiDirectionalLight: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the RTTI object at RVA 0x331d838 that GetRTTI addresses, bound by hint
extern const NiRTTI NiRTTI_NiDirectionalLight;

// NiLightBase: STANDIN GUESS(low); the same 0x140 size as NiLight, declaring the fields the compared code reads
class NiLightBase
{
public:
    // NiLightBase destructor: GUESS(low); declared only, bound by address
    virtual ~NiLightBase();

    // unk08: GUESS(low); members not recovered
    std::uint8_t unk08[0x74];  // 08
    // lightA: GUESS(low); the dword the update pass reads
    std::uint32_t lightA;  // 7C
    // unk80: GUESS(low); members not recovered
    std::uint8_t unk80[0x08];  // 80
    // lightB: GUESS(low); the dword the update pass reads
    std::uint32_t lightB;  // 88
    // unk8C: GUESS(low); members not recovered
    std::uint8_t unk8C[0x08];  // 8C
    // lightC: GUESS(low); the dword the update pass reads
    std::uint32_t lightC;  // 94
    // unk98: GUESS(low); padding up to the 0x140 size
    std::uint8_t unk98[0xA8];  // 98
};
static_assert(sizeof(NiLightBase) == 0x140, "NiLightBase size");

class NiDirectionalLight : public NiLightBase
{
public:
    NiDirectionalLight();
    virtual ~NiDirectionalLight();  // compared: 0xf046d0 (scalar deleting destructor; the listing calls the complete destructor, declared only)
    virtual void UpdateWorldData();  // compared: 0xf045c0
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xf04710

    // BaseUpdateWorldData: GUESS(low); the base pass the listing calls first, bound by address
    void BaseUpdateWorldData();

    // copyA..C: GUESS(low); the dwords the update pass writes
    std::uint32_t copyA;  // 140
    std::uint32_t copyB;  // 144
    std::uint32_t copyC;  // 148
    // unk14C: GUESS(low); padding up to the 0x158 size
    std::uint8_t unk14C[0x0C];  // 14C
};
static_assert(sizeof(NiDirectionalLight) == 0x158, "NiDirectionalLight size");
