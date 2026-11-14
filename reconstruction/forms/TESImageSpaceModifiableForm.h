// TESImageSpaceModifiableForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesimagespacemodifiableform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESImageSpaceModifiableForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// TESImageSpaceModifiableForm::ClearDataComponent, TESImageSpaceModifiableForm::InitializeDataComponent, TESImageSpaceModifiableForm::~TESImageSpaceModifiableForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent: GUESS(low)
// data08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class TESImageSpaceModifiableForm : public BaseFormComponent
{
public:
    TESImageSpaceModifiableForm();
    virtual void ClearDataComponent();  // compared: 0x1e8660
    virtual void InitializeDataComponent();  // compared: 0x1e8650
    virtual ~TESImageSpaceModifiableForm() {}  // compared: 0x1e8760 (scalar deleting destructor; target inlines this destructor)

    void* data08;  // 08
};
static_assert(sizeof(TESImageSpaceModifiableForm) == 0x10, "TESImageSpaceModifiableForm size");
