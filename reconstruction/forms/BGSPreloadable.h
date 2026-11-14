// BGSPreloadable declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgspreloadable
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSPreloadable: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// BGSPreloadable::ClearDataComponent, BGSPreloadable::CopyComponent, BGSPreloadable::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BaseFormComponent;

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class BGSPreloadable : public BaseFormComponent
{
public:
    virtual void ClearDataComponent();  // compared: 0x2601d0
    virtual void CopyComponent(BaseFormComponent* a_rhs);  // compared: 0x2601e0
    virtual void InitializeDataComponent();  // compared: 0x2601f0
};
static_assert(sizeof(BGSPreloadable) == 0x8, "BGSPreloadable size");
