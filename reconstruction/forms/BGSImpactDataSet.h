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
// BGSImpactDataSet: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"
inline BaseFormComponent::~BaseFormComponent() {}
class BGSPreloadable : public BaseFormComponent { public: ~BGSPreloadable() override {} void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; virtual void Preload(); };
struct ImpactEntry { const void* key; void* value; ImpactEntry* next; };
struct ImpactTail { ~ImpactTail(); std::uint32_t unknown00,capacity,freeCount,good; ImpactEntry* sentinel; std::uint64_t allocatorState; ImpactEntry* entries; };
struct ImpactMap { std::uint64_t unknown00; ImpactTail tail; };
class BGSImpactDataSet : public TESForm, public BGSPreloadable { public: BGSImpactDataSet(); ~BGSImpactDataSet() override; void InitItemImpl() override; void ClearData() override; ImpactMap impactMap; }; static_assert(sizeof(BGSImpactDataSet)==0x58,"impact data set size");
void DestroyImpactEntry(ImpactEntry*,void**); void ResolveImpactMap(void*,std::uint8_t,ImpactMap**); extern void* ImpactDataHandler; void MarkImpactSet(TESForm*,bool);
extern __declspec(thread) std::uint32_t MemoryTLS;
struct MemoryScope { std::uint32_t saved; MemoryScope():saved(MemoryTLS) { MemoryTLS=0x65; } ~MemoryScope(){MemoryTLS=saved;} };

