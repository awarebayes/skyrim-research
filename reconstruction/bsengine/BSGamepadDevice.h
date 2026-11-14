// BSGamepadDevice declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsgamepaddevice
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSGamepadDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIInputDevice, BSInputDevice: STANDIN EXE_RTTI
// BSGamepadDevice::Unk_0E, BSGamepadDevice::Unk_0C, BSGamepadDevice::ResetLEDColor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSIInputDevice::~BSIInputDevice, unknown08, unknown70: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSIInputDevice
{
public:
    virtual ~BSIInputDevice() = default;
};
static_assert(sizeof(BSIInputDevice) == 0x8, "BSIInputDevice size");

class BSInputDevice : public BSIInputDevice
{
public:
    std::uint8_t unknown08[0x68];  // 08
};
static_assert(sizeof(BSInputDevice) == 0x70, "BSInputDevice size");

class BSGamepadDevice : public BSInputDevice
{
public:
    virtual void Unk_0E();  // compared: 0xcfbde0
    virtual bool Unk_0C();  // compared: 0xcfc180
    virtual void ResetLEDColor();  // compared: 0xcfc1a0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown70[0x60];  // 70
};
static_assert(sizeof(BSGamepadDevice) == 0xD0, "BSGamepadDevice size");
