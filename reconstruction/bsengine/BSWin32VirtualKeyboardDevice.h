// BSWin32VirtualKeyboardDevice declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswin32virtualkeyboarddevice
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSWin32VirtualKeyboardDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIInputDevice, BSInputDevice, BSKeyboardDevice, BSVirtualKeyboardDevice: STANDIN EXE_RTTI
// BSWin32VirtualKeyboardDevice::Initialize, BSWin32VirtualKeyboardDevice::Release, BSWin32VirtualKeyboardDevice::Reset: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSIInputDevice::~BSIInputDevice, unknown08: GUESS(low)
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

class BSKeyboardDevice : public BSInputDevice
{
public:
};
static_assert(sizeof(BSKeyboardDevice) == 0x70, "BSKeyboardDevice size");

class BSVirtualKeyboardDevice : public BSKeyboardDevice
{
public:
};
static_assert(sizeof(BSVirtualKeyboardDevice) == 0x70, "BSVirtualKeyboardDevice size");

class BSWin32VirtualKeyboardDevice : public BSVirtualKeyboardDevice
{
public:
    virtual void Initialize();  // compared: 0xe12e60
    virtual void Release();  // compared: 0xe12e70
    virtual void Reset();  // compared: 0xe12e80
};
static_assert(sizeof(BSWin32VirtualKeyboardDevice) == 0x70, "BSWin32VirtualKeyboardDevice size");
