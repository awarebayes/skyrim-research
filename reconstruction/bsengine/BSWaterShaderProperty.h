// BSWaterShaderProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bswatershaderproperty
// Source exposure: mixed (names and declarations from community headers; base classes, offsets and
// the compared functions from the pinned image).
// Base form: shared header ../bsengine/BSShaderProperty.h for BSShaderProperty, BSShaderMaterial,
// BSRenderPass, NiStream and NiBinaryStream.
// BSWaterShaderProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// DoClearRenderPasses, SaveBinary, LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// waterFlags, unk8C, unk90, unkC0, unkD0: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares waterFlags as a 4-byte enumeration, unk8C as std::uint32_t, unk90 and unkD0 as std::uint64_t, unkC0 as BSRenderPass*; this file keeps unk90 and unkD0 as padding
// unkC8: GUESS(low); the community header names this slot simpleRenderPassList, but the image reads it as a pointer to an entry with a dword key at +0x18, so that name is not used here
// WaterMaterialEntry, unk000, key, ReleaseWaterEntry, InitScrapHeapGuard, BaseLinkObject, g_scrapHeapInitState: GUESS(low); invented here, the image gives only the offsets and the calls
// g_memoryManager: GUESS(low); the image passes its address as this to GetThreadScrapHeap
// MemoryManager, ScrapHeap: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares them in MemoryManager.h and ScrapHeap.h, only the members used are declared
// MemoryManager::GetThreadScrapHeap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares no argument, the image passes a zero second argument
// ScrapHeap::Deallocate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSRenderPass::ClearRenderPass, BSShaderProperty::SetMaterial, BSShaderProperty::SaveBinary, BSShaderProperty::DoClearRenderPasses: names from the shared header; the image calls them directly, the base LinkObject is reached through BaseLinkObject
// Public naming source notice:
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
#include "../bsengine/BSShaderProperty.h"

// ScrapHeap: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only Deallocate is declared
class ScrapHeap
{
public:
	void Deallocate(void* a_mem);
};

// MemoryManager: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only GetThreadScrapHeap is declared
class MemoryManager
{
public:
	ScrapHeap* GetThreadScrapHeap(std::uint32_t a_unk);
};

// WaterMaterialEntry: GUESS(low); the image reads one dword at 0x18 of the entry it holds at 0xC8
struct WaterMaterialEntry
{
	std::uint8_t unk000[0x18];  // 00
	std::int32_t key;           // 18
};

// ReleaseWaterEntry, InitScrapHeapGuard: GUESS(low); the image calls them with these argument registers, the names are invented
void ReleaseWaterEntry(WaterMaterialEntry** a_slot);
void InitScrapHeapGuard(MemoryManager* a_mm, std::int32_t* a_state);

// g_scrapHeapInitState: GUESS(low); the name is invented, the image gives only the address
extern std::int32_t g_scrapHeapInitState;
// g_memoryManager: GUESS(low); the image passes its address as this to GetThreadScrapHeap
extern MemoryManager g_memoryManager;

class BSWaterShaderProperty : public BSShaderProperty
{
public:
    // QShader: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    virtual std::uint32_t QShader() const;
	virtual void DoClearRenderPasses() override;
	virtual void SaveBinary(NiStream& a_stream) override;
	virtual void LinkObject(NiStream& a_stream);

	// BaseLinkObject: GUESS(low); stands in for the inherited LinkObject, which the shared headers do not declare; the image calls it at RVA 0x14e7430
	void BaseLinkObject(NiStream& a_stream);

	// waterFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); SaveBinary writes it as one 4-byte value
	std::uint32_t waterFlags;  // 88
	// unk8C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t unk8C;  // 8C
	// unk90: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); kept as padding up to the render pass pointer
	std::uint8_t unk90[0x30];  // 90
	// unkC0: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the render pass that DoClearRenderPasses releases and clears
	BSRenderPass* unkC0;  // C0
	// unkC8: GUESS(low); cache entry that ReleaseWaterEntry clears
	WaterMaterialEntry* unkC8;  // C8
	// unkD0: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); kept as padding to the declared size
	std::uint8_t unkD0[0x30];  // D0
};
static_assert(sizeof(BSWaterShaderProperty) == 0x100, "BSWaterShaderProperty size");
