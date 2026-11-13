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
// BGSProcedureTreeProcedure declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-a-bgsproceduretreeprocedure
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSProcedureTreeConditionalItem.h for
// BGSProcedureTreeConditionalItem.
// BGSProcedureTreeProcedure: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSTypedItem_VBGSProcedureTreeProcedure__VBGSProcedureTreeConditionalItem: STANDIN EXE_RTTI
// BGSProcedureTreeProcedure::procedure: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares BGSProcedureBase* at 0x10
// BGSProcedureTreeProcedure::Unk_02: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares void Unk_02(void), the listing takes the TESFile argument
// BGSProcedureTreeProcedure::Unk_0B, BGSProcedureTreeProcedure::Unk_08, BGSProcedureTreeProcedure::Unk_09: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares void, the listing returns a bool
// BGSProcedureTreeProcedure::Unk_0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares void Unk_0C(void), the listing takes the other item
// BGSProcedureBase: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSProcedureBase::Unk_00, BGSProcedureBase::Unk_01, BGSProcedureBase::Unk_02, BGSProcedureBase::Unk_03, BGSProcedureBase::Unk_04, BGSProcedureBase::Unk_05, BGSProcedureBase::Unk_06, BGSProcedureBase::Unk_07, BGSProcedureBase::Unk_08, BGSProcedureBase::Unk_09, BGSProcedureBase::Unk_0A, BGSProcedureBase::Unk_0B, BGSProcedureBase::Unk_0C, BGSProcedureBase::Unk_0D, BGSProcedureBase::Unk_0E, BGSProcedureBase::Unk_0F, BGSProcedureBase::Unk_10, BGSProcedureBase::Unk_11, BGSProcedureBase::Unk_12, BGSProcedureBase::Unk_13, BGSProcedureBase::Unk_14, BGSProcedureBase::Unk_15, BGSProcedureBase::Unk_16, BGSProcedureBase::Unk_17, BGSProcedureBase::Unk_18, BGSProcedureBase::Unk_19: GUESS(low); slots numbered by vtable index, only the slots the compared code calls have signatures
// Unk_4a6940: GUESS(low); the free function the compared code calls on the condition at +0x8
// unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/BGSProcedureTreeConditionalItem.h"

class BGSProcedureBase
{
public:
    virtual void Unk_00(void* a_owner);  // 00
    virtual void Unk_01(BGSProcedureBase* a_procedure);  // 01
    virtual void Unk_02();  // 02
    virtual void Unk_03();  // 03
    virtual void Unk_04();  // 04
    virtual void Unk_05(TESFile* a_mod);  // 05
    virtual void Unk_06();  // 06
    virtual void Unk_07();  // 07
    virtual void Unk_08();  // 08
    virtual void Unk_09();  // 09
    virtual void Unk_0A();  // 0A
    virtual void Unk_0B();  // 0B
    virtual void Unk_0C();  // 0C
    virtual void Unk_0D();  // 0D
    virtual void Unk_0E();  // 0E
    virtual void Unk_0F();  // 0F
    virtual void Unk_10();  // 10
    virtual void Unk_11();  // 11
    virtual void Unk_12();  // 12
    virtual void Unk_13();  // 13
    virtual void Unk_14();  // 14
    virtual bool Unk_15();  // 15
    virtual bool Unk_16();  // 16
    virtual void Unk_17();  // 17
    virtual void Unk_18();  // 18
    virtual bool Unk_19();  // 19
};

// Free function the compared code calls with the condition at +0x8 and the TESFile argument.
void Unk_4a6940(TESCondition* a_condition, TESFile* a_mod);

class BGSTypedItem_VBGSProcedureTreeProcedure__VBGSProcedureTreeConditionalItem : public BGSProcedureTreeConditionalItem
{
public:
};
static_assert(sizeof(BGSTypedItem_VBGSProcedureTreeProcedure__VBGSProcedureTreeConditionalItem) == 0x10, "BGSTypedItem_VBGSProcedureTreeProcedure__VBGSProcedureTreeConditionalItem size");

class BGSProcedureTreeProcedure : public BGSTypedItem_VBGSProcedureTreeProcedure__VBGSProcedureTreeConditionalItem
{
public:
    virtual std::uint8_t Unk_0F() const;
    bool Unk_0B();  // compared: 0x48a730
    bool Unk_08();  // compared: 0x48a7e0
    bool Unk_09();  // compared: 0x48a810
    void Unk_02(TESFile* a_mod);  // compared: 0x48a650
    void Unk_0C(BGSProcedureBase* a_other);  // compared: 0x48a760

    // members
    BGSProcedureBase* procedure;  // 10
};
static_assert(sizeof(BGSProcedureTreeProcedure) == 0x18, "BGSProcedureTreeProcedure size");
