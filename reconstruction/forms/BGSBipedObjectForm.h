// BGSBipedObjectForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsbipedobjectform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSBipedObjectForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// BGSBipedObjectForm::ClearDataComponent, BGSBipedObjectForm::InitializeDataComponent, BGSBipedObjectForm::~BGSBipedObjectForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent: GUESS(low)
// unk08, unknown0C: GUESS(low); unk08 is the dword the initialiser stores zero into
#pragma once

#include <cstdint>
#include <cstddef>

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class BGSBipedObjectForm : public BaseFormComponent
{
public:
    BGSBipedObjectForm();
    virtual void ClearDataComponent();  // compared: 0x1d20f0
    virtual void InitializeDataComponent();  // compared: 0x1d20e0
    virtual ~BGSBipedObjectForm();  // compared: 0x1d21f0 (scalar deleting destructor)

    std::uint32_t unk08;  // 08
    std::uint8_t unknown0C[0x4];  // 0C
};
static_assert(sizeof(BGSBipedObjectForm) == 0x10, "BGSBipedObjectForm size");
