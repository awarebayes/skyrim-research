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
// BGSSaveFormBuffer declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-a-bgssaveformbuffer
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSSaveFormBuffer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSSaveGameBuffer: STANDIN EXE_RTTI
// BGSSaveFormBuffer::GetActor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSSaveGameBuffer::GetForm, BGSSaveGameBuffer::GetReference: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Actor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::formType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); offset 0x1A matches NG
// FormType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); underlying type uint8 as NG declares
// FormType::ActorCharacter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); value 0x3E as NG declares
// BGSSaveGameBuffer::~BGSSaveGameBuffer, unknown08, unknown18, TESForm::unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class Actor;
class TESObjectREFR;
class TESForm;

enum class FormType : std::uint8_t
{
    ActorCharacter = 0x3E,
};

class TESForm
{
public:
    virtual ~TESForm() = default;
    std::uint8_t unknown08[0x12];  // 08
    FormType     formType;         // 1A
};
static_assert(offsetof(TESForm, formType) == 0x1A, "TESForm::formType offset");

class TESObjectREFR : public TESForm
{
};

class Actor : public TESObjectREFR
{
};

class BGSSaveGameBuffer
{
public:
    // SaveDataEndian: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); name only.
    // This target call passes four arguments rather than the community wrapper's two.
    // a_data, a_size, a_count, a_flags: GUESS(low); parameter names for the observed call shape.
    void SaveDataEndian(const void* a_data, std::uint32_t a_size, std::uint32_t a_count, std::uint32_t a_flags);
    virtual ~BGSSaveGameBuffer() = default;
    virtual TESForm*       GetForm();       // slot 01, declared only
    virtual TESObjectREFR* GetReference();  // slot 02, declared only
    std::uint8_t unknown08[0x10];           // 08
};
static_assert(sizeof(BGSSaveGameBuffer) == 0x18, "BGSSaveGameBuffer size");

class BGSSaveFormBuffer : public BGSSaveGameBuffer
{
public:
    virtual void* GetForm() const;
    virtual Actor* GetActor();  // compared: 0x639860

    std::uint8_t unknown18[0x10];
    // member: GUESS(low); accepted getter storage at offset 0x28
    void* member;  // 28
};
static_assert(sizeof(BGSSaveFormBuffer) == 0x30, "BGSSaveFormBuffer size");
