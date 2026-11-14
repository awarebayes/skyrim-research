// BGSSkinForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsskinform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSSkinForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// BGSSkinForm::ClearDataComponent, BGSSkinForm::InitializeDataComponent, BGSSkinForm::~BGSSkinForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class BGSSkinForm : public BaseFormComponent
{
public:
    BGSSkinForm();
    virtual void ClearDataComponent();  // compared: 0x1db8e0
    virtual void InitializeDataComponent();  // compared: 0x1db8d0
    virtual ~BGSSkinForm() {}  // compared: 0x1dbab0 (scalar deleting destructor)

    void* ptr08;  // 08
};
static_assert(sizeof(BGSSkinForm) == 0x10, "BGSSkinForm size");
