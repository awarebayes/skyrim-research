// BGSEntryPointFunctionDataActivateChoice declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s07-bgsentrypointfunctiondataactivatechoice
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSEntryPointFunctionData.h for BGSEntryPointFunctionData.
// BGSEntryPointFunctionDataActivateChoice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSEntryPointFunctionDataActivateChoice::Unk_05, BGSEntryPointFunctionDataActivateChoice::SetPerk, BGSEntryPointFunctionDataActivateChoice::GetPerk: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSPerk: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// perk10, field22: GUESS(low)
// unknown08, unknown18, unknown24: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/BGSEntryPointFunctionData.h"

class BGSPerk;

class BGSEntryPointFunctionDataActivateChoice : public BGSEntryPointFunctionData
{
public:
    virtual std::uint16_t Unk_05();  // compared: 0x38ea80
    virtual void SetPerk(BGSPerk* a_perk);  // compared: 0x38ea90
    virtual BGSPerk* GetPerk();  // compared: 0x38eaa0

    std::uint8_t unknown08[0x8];  // 08
    BGSPerk* perk10;  // 10
    std::uint8_t unknown18[0xA];  // 18
    std::uint16_t field22;  // 22
    std::uint8_t unknown24[0x4];  // 24
};
static_assert(sizeof(BGSEntryPointFunctionDataActivateChoice) == 0x28, "BGSEntryPointFunctionDataActivateChoice size");
