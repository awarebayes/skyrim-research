// TESQualityForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesqualityform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESQualityForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// TESQualityForm::ClearDataComponent, TESQualityForm::InitializeDataComponent, TESQualityForm::~TESQualityForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent, unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class TESQualityForm : public BaseFormComponent
{
public:
    TESQualityForm();
    virtual void ClearDataComponent();  // compared: 0x1ef660
    virtual void InitializeDataComponent();  // compared: 0x1ef650
    virtual ~TESQualityForm() {}  // compared: 0x1ef6e0 (scalar deleting destructor)

    std::uint32_t value08;      // 08
    std::uint8_t  unknown0C[0x4];  // 0C
};
static_assert(sizeof(TESQualityForm) == 0x10, "TESQualityForm size");
