// BGSEntryPointFunctionDataText::GetType, build sse-steam-1-7-104, RVA 0x38eed0, 6 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"medium","kind":"public","repository":"meh321/AddressLibraryDatabase","revision":"0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91","source":"meh321"},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// BGSEntryPointFunctionDataText: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// BGSEntryPointFunctionData, BGSEntryPointFunctionData::~BGSEntryPointFunctionData,
// LoadFunctionData, ResolveForms, SetPerk, GetPerk: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESFile;
class BGSPerk;
class BGSEntryPointFunctionData {
public:
    BGSEntryPointFunctionData();
    virtual ~BGSEntryPointFunctionData() {}
    virtual std::uint32_t GetType() const = 0;
    virtual bool LoadFunctionData(TESFile*) = 0;
    virtual void ResolveForms(TESFile*);
    // Unk_04, Unk_05: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    virtual void Unk_04();
    virtual void Unk_05();
    virtual void SetPerk(BGSPerk*);
    virtual BGSPerk* GetPerk();
};
// BSFixedString, BSFixedString::~BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: GUESS(low); pooled string pointer.
class BSFixedString { public: ~BSFixedString(); const char* value; };
class BGSEntryPointFunctionDataText : public BGSEntryPointFunctionData {
public:
    // BGSEntryPointFunctionDataText::BGSEntryPointFunctionDataText: GUESS(low); retained for vftable emission.
    BGSEntryPointFunctionDataText();
    // BGSEntryPointFunctionDataText::~BGSEntryPointFunctionDataText,
    // BGSEntryPointFunctionDataText::text: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    ~BGSEntryPointFunctionDataText() override = default;
    std::uint32_t GetType() const override;
    bool LoadFunctionData(TESFile*) override;
    BSFixedString text;
};
static_assert(sizeof(BGSEntryPointFunctionDataText) == 0x10, "function data text size");
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
