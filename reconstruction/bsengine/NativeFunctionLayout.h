// Build: sse-steam-1-7-104
// Source exposure: mixed (pinned community declarations and local target analysis).
// Drafted by GPT-6.1 Sol; p106 shared represented-layout recovery.
// Labels: v2
// NativeFunctionLayout, NativeFunctionBaseLayout, ScriptFunctionLayout, ScriptRefCountLayout,
// ScriptStringLayout, ScriptTypeLayout, ScriptDescriptorLayout: GUESS(low) STANDIN
// Fields through docString adapt the corresponding IFunction, NativeFunctionBase,
// BSIntrusiveRefCounted and VDescTable declarations in the pinned community headers.
// Source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a
// Paths: include/RE/I/IFunction.h, include/RE/N/NativeFunctionBase.h,
// include/RE/B/BSIntrusiveRefCounted.h, include/RE/V/VDescTable.h.
// Field layouts: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Callback representation differs from the modern community NativeFunction declaration:
// the pinned image's slot-21 methods test one pointer at offset 0x50, and its
// dispatch methods call that pointer. The callback signature below is a guess.
// NativeFunction and NativeLatentFunction owner spellings: EXE_RTTI
// callback, Callback: GUESS(low)
// No methods or original template argument identities are reconstructed here.
// Shared base destructor visits string fields at 0x48, 0x20, 0x18, 0x10
// and the descriptor table at 0x30. Size and offsets remain layout claims only.
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
#pragma once
#include <cstdint>
#include <cstddef>

namespace ResearchLayouts {
struct ScriptRefCountLayout {
    volatile std::uint32_t referenceCount;
};
struct ScriptStringLayout {
    const char* entry;
};
struct ScriptTypeLayout {
    std::uintptr_t value;
};
struct ScriptDescriptorLayout {
    void* entries;
    std::uint16_t parameterCount;
    std::uint16_t totalEntries;
};
class ScriptFunctionLayout : public ScriptRefCountLayout {
public:
    virtual ~ScriptFunctionLayout();
};
class NativeFunctionBaseLayout : public ScriptFunctionLayout {
public:
    ~NativeFunctionBaseLayout() override;
    ScriptStringLayout name;
    ScriptStringLayout objectName;
    ScriptStringLayout stateName;
    ScriptTypeLayout returnType;
    ScriptDescriptorLayout descriptors;
    bool isStatic;
    bool callableFromTasklet;
    bool isLatent;
    std::uint32_t userFlags;
    ScriptStringLayout docString;
};
class NativeFunctionLayout : public NativeFunctionBaseLayout {
public:
    ~NativeFunctionLayout() override;
    using Callback = void (*)();
    Callback callback;
};
static_assert(sizeof(ScriptRefCountLayout) == 4, "reference count layout");
static_assert(sizeof(ScriptFunctionLayout) == 0x10, "script function base");
static_assert(sizeof(ScriptDescriptorLayout) == 0x10, "descriptor table");
static_assert(sizeof(NativeFunctionBaseLayout) == 0x50, "native function base");
static_assert(sizeof(NativeFunctionLayout) == 0x58, "native callback specialization");
static_assert(offsetof(NativeFunctionBaseLayout, name) == 0x10, "name offset");
static_assert(offsetof(NativeFunctionBaseLayout, descriptors) == 0x30, "descriptors offset");
static_assert(offsetof(NativeFunctionBaseLayout, userFlags) == 0x44, "user flags offset");
static_assert(offsetof(NativeFunctionBaseLayout, docString) == 0x48, "documentation offset");
static_assert(offsetof(NativeFunctionLayout, callback) == 0x50, "callback offset");
}
