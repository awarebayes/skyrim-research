// TESTexture declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-testexture
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent: STANDIN EXE_RTTI
// TESTexture::GetMaxAllowedSize, TESTexture::ClearDataComponent, TESTexture::GetDefaultPath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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
    virtual std::uint32_t GetMaxAllowedSize();  // compared: 0x146760
    virtual void ClearDataComponent();  // compared: 0x1f2b20
    virtual const char* GetDefaultPath() const;  // compared: 0x1f3320

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(TESTexture) == 0x10, "TESTexture size");
