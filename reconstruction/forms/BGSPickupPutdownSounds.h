// BGSPickupPutdownSounds declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgspickupputdownsounds
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSPickupPutdownSounds: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// BGSPickupPutdownSounds::ClearDataComponent, BGSPickupPutdownSounds::InitializeDataComponent, BGSPickupPutdownSounds::~BGSPickupPutdownSounds: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// field08, field10: GUESS(low); the two qwords InitializeDataComponent zeroes
#pragma once

#include <cstdint>
#include <cstddef>

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class BGSPickupPutdownSounds : public BaseFormComponent
{
public:
    BGSPickupPutdownSounds();
    virtual void ClearDataComponent();  // compared: 0x1db710
    virtual void InitializeDataComponent();  // compared: 0x1db6f0
    virtual ~BGSPickupPutdownSounds();  // compared: 0x1db880 (scalar deleting destructor)

    std::uint64_t field08;  // 08
    std::uint64_t field10;  // 10
};
static_assert(sizeof(BGSPickupPutdownSounds) == 0x18, "BGSPickupPutdownSounds size");
