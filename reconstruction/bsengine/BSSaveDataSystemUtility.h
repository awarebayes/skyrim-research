// BSSaveDataSystemUtility declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s30-bsteventsource-vbssavedatae-bssavedatasystemutili
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSSaveDataSystemUtility: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSSaveDataSystemUtility::Unk_0B, BSSaveDataSystemUtility::Unk_0A: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

// LookupValue: GUESS(low); the callee at RVA 0xed4a30, bound by the unit's bind-hints.json
bool LookupValue(void* a_obj, std::uint32_t* a_out);

class BSSaveDataSystemUtility
{
public:
    virtual std::uint64_t* Unk_0B(std::uint64_t* a_out);  // compared: 0x159af80
    virtual std::uint32_t Unk_0A(void* a_obj);  // compared: 0x159ab30
    // Unk_05, Unk_07, Unk_08: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the listings of Unk_07 and Unk_08 return a bool, not the void the sheet declares
    virtual void Unk_05();  // compared: 0x159aa00
    virtual bool Unk_07();  // compared: 0x159a9f0
    virtual bool Unk_08();  // compared: 0x159a9e0

    std::uint8_t unknown08[0x220];  // 08
};
static_assert(sizeof(BSSaveDataSystemUtility) == 0x228, "BSSaveDataSystemUtility size");
