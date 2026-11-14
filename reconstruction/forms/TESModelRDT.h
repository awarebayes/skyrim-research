// TESModelRDT declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesmodelrdt
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESModelRDT: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent, TESModel: STANDIN EXE_RTTI
// TESModelRDT::~TESModelRDT: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class TESModelRDT : public TESModel
{
public:
    TESModelRDT();
    virtual ~TESModelRDT();  // compared: 0x1dfd40 (scalar deleting destructor)
};
static_assert(sizeof(TESModelRDT) == 0x28, "TESModelRDT size");
