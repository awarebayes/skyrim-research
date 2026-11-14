// TESIcon declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesicon
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESIcon: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent, TESTexture: STANDIN EXE_RTTI
// TESIcon::GetDefaultPath, TESIcon::~TESIcon: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class TESTexture : public BaseFormComponent
{
public:
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(TESTexture) == 0x10, "TESTexture size");

class TESIcon : public TESTexture
{
public:
    TESIcon();
    virtual const char* GetDefaultPath() const;  // compared: 0x1e85e0
    virtual ~TESIcon();  // compared: 0x1e85f0 (scalar deleting destructor)
};
static_assert(sizeof(TESIcon) == 0x10, "TESIcon size");
