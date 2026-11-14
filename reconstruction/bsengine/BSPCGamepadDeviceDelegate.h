// BSPCGamepadDeviceDelegate declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bspcgamepaddevicedelegate
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSPCGamepadDeviceDelegate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIInputDevice, BSInputDevice, BSGamepadDevice: STANDIN EXE_RTTI
// BSPCGamepadDeviceDelegate::Reset, BSPCGamepadDeviceDelegate::Initialize, BSPCGamepadDeviceDelegate::Process: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSIInputDevice::~BSIInputDevice, unknown08, unknown70, unknownD0: GUESS(low)
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
    std::uint8_t unknown70[0x60];  // 70
};
static_assert(sizeof(BSGamepadDevice) == 0xD0, "BSGamepadDevice size");

class BSPCGamepadDeviceDelegate : public BSGamepadDevice
{
public:
    virtual void Reset();  // compared: 0xe12470
    virtual void Initialize();  // compared: 0xe12480
    virtual void Process(float a_arg1);  // compared: 0xe124a0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknownD0[0x8];  // D0
};
static_assert(sizeof(BSPCGamepadDeviceDelegate) == 0xD8, "BSPCGamepadDeviceDelegate size");
