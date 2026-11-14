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
// Adapted from published p106 represented declaration reconstruction/bsengine/NativeFunctionLayout.h.
// Include spelling and local type names changed; all represented fields, bases, size and offset assertions retained.
// ScriptRefCountStorageLayout, ScriptStringStorageLayout, ScriptTypeStorageLayout, ScriptDescriptorStorageLayout, ScriptFunctionStorageLayout, NativeFunctionBaseStorageLayout, NativeFunctionStorageLayout: GUESS(medium) STANDIN; compilation-local represented type aliases.
#pragma once
#include <cstdint>
#include <cstddef>

namespace ResearchLayouts {
struct ScriptRefCountStorageLayout {
    volatile std::uint32_t referenceCount;
};
struct ScriptStringStorageLayout {
    const char* entry;
};
struct ScriptTypeStorageLayout {
    std::uintptr_t value;
};
struct ScriptDescriptorStorageLayout {
    void* entries;
    std::uint16_t parameterCount;
    std::uint16_t totalEntries;
};
class ScriptFunctionStorageLayout : public ScriptRefCountStorageLayout {
public:
    virtual ~ScriptFunctionStorageLayout();
};
class NativeFunctionBaseStorageLayout : public ScriptFunctionStorageLayout {
public:
    ~NativeFunctionBaseStorageLayout() override;
    ScriptStringStorageLayout name;
    ScriptStringStorageLayout objectName;
    ScriptStringStorageLayout stateName;
    ScriptTypeStorageLayout returnType;
    ScriptDescriptorStorageLayout descriptors;
    bool isStatic;
    bool callableFromTasklet;
    bool isLatent;
    std::uint32_t userFlags;
    ScriptStringStorageLayout docString;
};
class NativeFunctionStorageLayout : public NativeFunctionBaseStorageLayout {
public:
    ~NativeFunctionStorageLayout() override;
    using Callback = void (*)();
    Callback callback;
};
static_assert(sizeof(ScriptRefCountStorageLayout) == 4, "reference count layout");
static_assert(sizeof(ScriptFunctionStorageLayout) == 0x10, "script function base");
static_assert(sizeof(ScriptDescriptorStorageLayout) == 0x10, "descriptor table");
static_assert(sizeof(NativeFunctionBaseStorageLayout) == 0x50, "native function base");
static_assert(sizeof(NativeFunctionStorageLayout) == 0x58, "native callback specialization");
static_assert(offsetof(NativeFunctionBaseStorageLayout, name) == 0x10, "name offset");
static_assert(offsetof(NativeFunctionBaseStorageLayout, descriptors) == 0x30, "descriptors offset");
static_assert(offsetof(NativeFunctionBaseStorageLayout, userFlags) == 0x44, "user flags offset");
static_assert(offsetof(NativeFunctionBaseStorageLayout, docString) == 0x48, "documentation offset");
static_assert(offsetof(NativeFunctionStorageLayout, callback) == 0x50, "callback offset");
}
