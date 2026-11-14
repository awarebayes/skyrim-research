// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (community headers and pinned-image analysis).
// Drafted by gpt-6.1-sol, Engineer p105 box3. Adapted bodies: none.
// Declarations adapt CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a (MIT).
// Helper spellings and local variable names are inferred; individual labels accompany declarations.
// MIT License
// 
// Copyright (c) 2018 Ryan-rsm-McKenzie
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// BSWin32MouseDevice: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
class BSIInputDevice { public: virtual ~BSIInputDevice() {} virtual void Initialize(); virtual void Process(float); virtual void Release(); virtual void Mapping0(); virtual void Mapping1(); virtual void Mapping2(); virtual bool IsEnabled() const; virtual void Reset(); };
struct ButtonMapTail { ~ButtonMapTail(); std::uint32_t unknown00,capacity,freeCount,good; void* sentinel; std::uint64_t allocatorState; void* entries; };
struct NameMapTail { ~NameMapTail(); std::uint32_t unknown00,capacity,freeCount,good; void* sentinel; std::uint64_t allocatorState; void* entries; };
struct ButtonMap { std::uint64_t unknown00; ButtonMapTail tail; };
struct NameMap { std::uint64_t unknown00; NameMapTail tail; };
class BSInputDevice : public BSIInputDevice { public: ~BSInputDevice() override { ResetButtonMaps(); } void ResetButtonMaps(); std::uint32_t device; ButtonMap deviceButtons; NameMap buttonNameIDMap; };
static_assert(sizeof(BSInputDevice)==0x70,"input device size");
class DirectInputDevice { public: virtual void Slot0(); virtual void Slot1(); virtual void Slot2(); virtual void Slot3(); virtual void Slot4(); virtual void Slot5(); virtual void Slot6(); virtual void Slot7(); virtual void Slot8(); virtual void Slot9(); virtual void Slot10(); virtual void SetDataFormat(const void*); virtual void Slot12(); virtual void SetCooperativeLevel(void*,std::uint32_t); };
class BSMouseDevice : public BSInputDevice { public: ~BSMouseDevice() override {} bool backgroundMouse; };
struct MouseState { std::int32_t x,y,z; std::uint8_t buttons[8]; };
class BSWin32MouseDevice : public BSMouseDevice { public: BSWin32MouseDevice(); ~BSWin32MouseDevice() override; void Initialize() override; DirectInputDevice* dInputDevice; MouseState previous,next; bool notInitialized; std::uint32_t lockThread,lockCount; }; static_assert(sizeof(BSWin32MouseDevice)==0xB8,"win32 mouse size");
extern void* DirectInputManager; extern const std::uint64_t MouseGUID[]; extern const std::uint64_t MouseDataFormat[]; extern bool BackgroundMouseSetting;
DirectInputDevice* CreateMouseDevice(void*,const void*);
extern "C" __declspec(dllimport) void* __stdcall GetActiveWindow();

