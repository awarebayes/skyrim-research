// TESLoadScreen type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESLoadScreen.h.
// The shape of ClearData follows the sibling's TESLoadScreen::ClearData (clear the screen data, then the
// base form). Layouts of the stand-ins are not claimed. Adapted bodies: none declared.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/tesloadscreen.cpp:89 (shape only; the target clears a condition list and a camera path model)
// TESLoadScreen, TESLoadScreen::ClearData, ::conditions, ::loadNIFData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESLoadScreen::LoadNIFData, ::cameraPath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// LoadNIFData::unk00: GUESS(low); the members before cameraPath are one opaque block here
// TESLoadScreen::unk30: GUESS(low); stands for loadingText
// TESCondition, TESModel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layouts reduced to their sizes
// TESCondition::head: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; its type is not claimed
// TESCondition::Clear: GUESS(low); the callee at RVA 0x4a6d90 that ClearData calls with this + 0x20
// TESModel::~TESModel, ::InitializeDataComponent, ::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only ClearDataComponent is called
// TESModel::unk08: GUESS(low); the members of TESModel are not recovered
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESCondition {
public:
    void Clear();

    void* head;  // 00
};

class TESModel : public BaseFormComponent {
public:
    ~TESModel() override;
    void InitializeDataComponent() override;  // 01
    void ClearDataComponent() override;       // 02

    std::uint8_t unk08[0x20];  // 08
};
static_assert(sizeof(TESModel) == 0x28, "layout");

class TESLoadScreen : public TESForm {
public:
    struct LoadNIFData {
        std::uint8_t unk00[0x28];  // 00
        TESModel     cameraPath;   // 28
    };
    static_assert(sizeof(LoadNIFData) == 0x50, "layout");

    void ClearData() override;  // 05

    TESCondition  conditions;   // 20
    LoadNIFData*  loadNIFData;  // 28
    std::uint64_t unk30;        // 30
};
static_assert(sizeof(TESLoadScreen) == 0x38, "layout");
