// BSWaterShaderProperty functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bswatershaderproperty
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611122314-2).
// Compared functions:
//   RVA 0x152d190, 62 bytes: BSWaterShaderProperty::DoClearRenderPasses
//   RVA 0x152c410, 82 bytes: BSWaterShaderProperty::SaveBinary
//   RVA 0x152c370, 123 bytes: BSWaterShaderProperty::LinkObject
// Not compared in this unit (near-miss, see task directory): RVA 0x152ce50 ForEachTexture,
// RVA 0x152cd00 Unk_2C.
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
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
#include "BSWaterShaderProperty.h"

// RVA 0x152d190, 62 bytes
void BSWaterShaderProperty::DoClearRenderPasses()
{
    ReleaseWaterEntry(&unkC8);
    if (unkC0 != nullptr) {
        unkC0->ClearRenderPass();
        unkC0 = nullptr;
    }
    BSShaderProperty::DoClearRenderPasses();
}

// RVA 0x152c410, 82 bytes
void BSWaterShaderProperty::SaveBinary(NiStream& a_stream)
{
    BSShaderProperty::SaveBinary(a_stream);
    std::uint32_t componentSize = sizeof(waterFlags);
    a_stream.oStr->binary_write(&waterFlags, sizeof(waterFlags), &componentSize, 1);
}

// RVA 0x152c370, 123 bytes
void BSWaterShaderProperty::LinkObject(NiStream& a_stream)
{
    BaseLinkObject(a_stream);
    BSShaderMaterial* previous = material;
    material = nullptr;
    BSShaderProperty::SetMaterial(previous, false);
    if (previous != nullptr) {
        previous->~BSShaderMaterial();
        if (g_scrapHeapInitState != 2) {
            InitScrapHeapGuard(&g_memoryManager, &g_scrapHeapInitState);
        }
        g_memoryManager.GetThreadScrapHeap(0)->Deallocate(previous);
    }
}


// Retained generated leaf; its byte-match evidence is renewed with this unit.
// QShader: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
std::uint32_t BSWaterShaderProperty::QShader() const
{
    return 0x11;
}
