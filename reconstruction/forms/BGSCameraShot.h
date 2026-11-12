// BGSCameraShot type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSCameraShot, BGSCameraShot::InitializeData, BGSCameraShot::~BGSCameraShot, BGSCameraShot::data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// CAMERA_SHOT_DATA: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's enum types are plain integers here
// TESModel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG slots 04 to 06 (GetModel, SetModel, GetAsModelTextureSwap) as placeholders; size 0x28
// TESModel::modelData: GUESS(low); filler bytes for model, textures, addons and counts
// TESImageSpaceModifiableForm, TESImageSpaceModifiableForm::imageSpaceModifying: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); BaseFormComponent base and one pointer, size 0x10
// BGSCameraShot::unk84: GUESS(low); opaque bytes for pad84 and the unk88 to unkB8 members (offset 0x84 to 0xC0)
// BGSCameraShot::BGSCameraShot: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, defined only so the unit emits the vftables and the deleting destructor
// BGSCameraShot::~BGSCameraShot: declared and not defined so that the deleting destructor calls the plain one; bound by hint to 0x3189e0
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESImageSpaceModifier;

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

class TESImageSpaceModifiableForm : public BaseFormComponent {
public:
    ~TESImageSpaceModifiableForm() override;                  // 00
    void InitializeDataComponent() override;                  // 01
    void ClearDataComponent() override;                       // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;    // 03

    TESImageSpaceModifier* imageSpaceModifying;  // 08
};
static_assert(sizeof(TESImageSpaceModifiableForm) == 0x10, "layout");

struct CAMERA_SHOT_DATA {
    std::uint32_t cameraAction;                // 00
    std::uint32_t location;                    // 04
    std::uint32_t target;                      // 08
    std::uint32_t flags;                       // 0C
    float         playerTimeMult;              // 10
    float         targetTimeMult;              // 14
    float         globalTimeMult;              // 18
    float         maxTime;                     // 1C
    float         minTime;                     // 20
    float         targetPercentBetweenActors;  // 24
    float         nearTargetDistance;          // 28
};
static_assert(sizeof(CAMERA_SHOT_DATA) == 0x2C, "layout");

class BGSCameraShot :
    public TESForm,                      // 00
    public TESModel,                     // 20
    public TESImageSpaceModifiableForm   // 48
{
public:
    BGSCameraShot();
    ~BGSCameraShot() override;  // 00

    void InitializeData() override;  // 04

    CAMERA_SHOT_DATA data;       // 58
    std::uint8_t     unk84[0x3C];  // 84
};
static_assert(sizeof(BGSCameraShot) == 0xC0, "layout");
