// BSWin32KeyboardDevice declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswin32keyboarddevice
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSWin32KeyboardDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIInputDevice, BSInputDevice, BSKeyboardDevice: STANDIN EXE_RTTI
// BSWin32KeyboardDevice::Unk_09, BSWin32KeyboardDevice::Unk_0A: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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

class BSKeyboardDevice : public BSInputDevice
{
public:
};
static_assert(sizeof(BSKeyboardDevice) == 0x70, "BSKeyboardDevice size");

class BSWin32KeyboardDevice : public BSKeyboardDevice
{
public:
    virtual void Unk_09();  // compared: 0xe12c20
    virtual void Unk_0A();  // compared: 0xe12c30

    // Padding up to the class size; the compared bodies read no member.
    std::uint8_t unknown70[0x300];  // 70
};
static_assert(sizeof(BSWin32KeyboardDevice) == 0x370, "BSWin32KeyboardDevice size");
