// TESClass declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s02-tesform-tesclass
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESClass: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESClass::GetMaximumTrainingLevel: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESClass::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown20: GUESS(low)
// unk50, unk58, unk60, trainingLevel, trainingSkill, unk70: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESClass : public TESForm
{
public:
    std::uint8_t GetMaximumTrainingLevel();  // compared: 0x3b2b10; TODO signature: no community declaration, read it from the listing
    virtual void InitializeData();  // compared: 0x3b2890

    std::uint8_t unknown20[0x30];  // 20
    union {
        std::uint64_t unk50;  // 50
        struct {
            std::uint8_t unknown50[0x5];
            std::uint8_t maximumTrainingLevel;  // 55
            std::uint8_t unknown56[0x2];
        };
    };
    std::uint64_t unk58;  // 58
    std::uint64_t unk60;  // 60
    union {
        std::uint64_t unk68;  // 68
        struct {
            float trainingLevel;  // 68
            std::uint32_t trainingSkill;  // 6C
        };
    };
    std::uint32_t unk70;  // 70
};
