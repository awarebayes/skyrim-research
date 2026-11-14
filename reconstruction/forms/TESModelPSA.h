// TESModelPSA declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesmodelpsa
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESModelPSA: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent, TESModel: STANDIN EXE_RTTI
// TESModelPSA::~TESModelPSA: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class TESModel : public BaseFormComponent
{
public:
    std::uint8_t unknown08[0x20];  // 08
};
static_assert(sizeof(TESModel) == 0x28, "TESModel size");

class TESModelPSA : public TESModel
{
public:
    TESModelPSA();
    virtual ~TESModelPSA();  // compared: 0x38af60 (scalar deleting destructor)
};
static_assert(sizeof(TESModelPSA) == 0x28, "TESModelPSA size");
