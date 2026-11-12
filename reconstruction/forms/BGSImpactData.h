// BGSImpactData type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSImpactData, BGSImpactData::InitializeData, BGSImpactData::data, BGSImpactData::decalTextureSet, BGSImpactData::decalTextureSet2, BGSImpactData::sound1, BGSImpactData::sound2, BGSImpactData::hazard: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IMPACT_DATA_DATA: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's enum types (ORIENTATION, SOUND_LEVEL, Flag, ImpactResult) are plain integers here
// BGSTextureSet, BGSSoundDescriptorForm, BGSHazard: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
// TESModel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG slots 04 to 06 (GetModel, SetModel, GetAsModelTextureSwap) as placeholders; size 0x28
// TESModel::modelData: GUESS(low); filler bytes for model, textures, addons and counts
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSTextureSet;
class BGSSoundDescriptorForm;
class BGSHazard;

class TESModel : public BaseFormComponent {
public:
    ~TESModel() override;                                    // 00
    void InitializeDataComponent() override;                 // 01
    void ClearDataComponent() override;                      // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;   // 03
    virtual const char* GetModel() const;                    // 04
    virtual void        SetModel(const char* a_model);       // 05
    virtual void*       GetAsModelTextureSwap();             // 06

    std::uint8_t modelData[0x20];  // 08
};
static_assert(sizeof(TESModel) == 0x28, "layout");

struct IMPACT_DATA_DATA {
    float         effectDuration;   // 00
    std::uint32_t orient;           // 04
    float         angleThreshold;   // 08
    float         placementRadius;  // 0C
    std::uint32_t soundLevel;       // 10
    std::uint8_t  flags;            // 14
    std::uint8_t  resultOverride;   // 15
    std::uint16_t unk16;            // 16
};
static_assert(sizeof(IMPACT_DATA_DATA) == 0x18, "layout");

class BGSImpactData :
    public TESForm,  // 00
    public TESModel  // 20
{
public:
    void InitializeData() override;  // 04

    IMPACT_DATA_DATA        data;              // 48
    BGSTextureSet*          decalTextureSet;   // 60
    BGSTextureSet*          decalTextureSet2;  // 68
    BGSSoundDescriptorForm* sound1;            // 70
    BGSSoundDescriptorForm* sound2;            // 78
    BGSHazard*              hazard;            // 80
};
