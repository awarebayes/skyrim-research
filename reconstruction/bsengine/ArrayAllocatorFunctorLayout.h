// Build: sse-steam-1-7-104
// Source exposure: mixed (community declarations and pinned image analysis).
// Drafted by GPT-6.1 Sol; p106 shared layout recovery.
// Labels: v2
// Interface declarations adapt CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/B/BSTArray.h.
// IAllocatorFunctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ArrayAllocatorFunctorLayout, allocator: GUESS(medium) STANDIN
// BSTArrayAllocatorFunctor: EXE_RTTI
// All 29 selected target specializations have virtual operations which load the
// allocator pointer from offset 8 before invoking their allocator implementation.
// Allocator type is a template parameter, not storage allocated to set a size.
// No allocator or array-operation implementation is copied or reconstructed.
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
class IAllocatorFunctor {
public:
    virtual bool Allocate(std::uint32_t count, std::uint32_t elementSize) = 0;
    virtual bool Reallocate(std::uint32_t minimum, std::uint32_t frontCount,
                            std::uint32_t shiftCount, std::uint32_t backCount,
                            std::uint32_t elementSize) = 0;
    virtual void Deallocate() = 0;
    virtual ~IAllocatorFunctor();
};
template<class Allocator>
class ArrayAllocatorFunctorLayout : public IAllocatorFunctor {
public:
    bool Allocate(std::uint32_t count, std::uint32_t elementSize) override;
    bool Reallocate(std::uint32_t minimum, std::uint32_t frontCount,
                    std::uint32_t shiftCount, std::uint32_t backCount,
                    std::uint32_t elementSize) override;
    void Deallocate() override;
    ~ArrayAllocatorFunctorLayout() override;
    Allocator* allocator;
};
static_assert(sizeof(IAllocatorFunctor) == 8, "allocator interface");
static_assert(sizeof(ArrayAllocatorFunctorLayout<void>) == 16, "allocator functor");
static_assert(offsetof(ArrayAllocatorFunctorLayout<void>, allocator) == 8, "allocator reference");
}
