// BGSMenuIcon represented declarations, build sse-steam-1-7-104.
// Labels: v2
// Origin: original reconstruction
// Source exposure: mixed; pinned public declarations and local analysis.
// BGSMenuIcon: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include "TESForm.h"
// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
inline BaseFormComponent::~BaseFormComponent() {}
// BSFixedString, BSFixedString::~BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: GUESS(low); the pooled string pointer at the observed member offset.
class BSString;
class BSFixedString {
public:
    ~BSFixedString();
    const char* value;
};

// TESFullName::~TESFullName, TESFullName::InitializeDataComponent, TESFullName::ClearDataComponent,
// TESFullName::CopyComponent, TESFullName::GetFullNameLength, TESFullName::GetFullName, TESFullName::fullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESFullName : public BaseFormComponent {
public:
    TESFullName();
    ~TESFullName() override {}
    void InitializeDataComponent() override;
    void ClearDataComponent() override;
    void CopyComponent(BaseFormComponent*) override;
    virtual std::uint32_t GetFullNameLength() const;
    virtual const char* GetFullName() const;
    BSFixedString fullName;
};
// TESTexture::~TESTexture, TESTexture::InitializeDataComponent, TESTexture::ClearDataComponent,
// TESTexture::CopyComponent, TESTexture::GetMaxAllowedSize, TESTexture::GetAsNormalFile, TESTexture::GetDefaultPath, TESTexture::textureName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESTexture : public BaseFormComponent {
public:
    TESTexture();
    ~TESTexture() override;
    void InitializeDataComponent() override;
    void ClearDataComponent() override;
    void CopyComponent(BaseFormComponent*) override;
    virtual std::uint32_t GetMaxAllowedSize();
    virtual const char* GetAsNormalFile(BSString&) const;
    virtual const char* GetDefaultPath() const;
    BSFixedString textureName;
};
static_assert(sizeof(TESFullName) == 0x10, "full-name component size");
static_assert(sizeof(TESTexture) == 0x10, "texture component size");

// TESIcon: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESIcon : public TESTexture { public: TESIcon(); ~TESIcon() override; const char* GetDefaultPath() const override; };

class BGSMenuIcon : public TESForm, public TESIcon {
public:
    BGSMenuIcon();
    ~BGSMenuIcon() override;
    
};
static_assert(sizeof(BGSMenuIcon) == 0x30, "represented size");
// Public declaration source notice:
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
