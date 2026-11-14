// BSUIScaleformData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsuiscaleformdata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSUIScaleformData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// IUIMessageData: STANDIN EXE_RTTI
// BSUIScaleformData::~BSUIScaleformData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IUIMessageData::~IUIMessageData, unknown08, unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class IUIMessageData
{
public:
    virtual ~IUIMessageData() = default;
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(IUIMessageData) == 0x10, "IUIMessageData size");

class BSUIScaleformData : public IUIMessageData
{
public:
    BSUIScaleformData();
    virtual ~BSUIScaleformData();  // compared: 0x1169040 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(BSUIScaleformData) == 0x18, "BSUIScaleformData size");
