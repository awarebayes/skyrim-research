// Build: sse-steam-1-7-104
// Source exposure: mixed (community declarations and independently bound target RTTI).
// Drafted by GPT-6.1 Sol; p104b shared represented-base recovery.
// Labels: v2
// Code origin: declarations adapted from the pinned community headers; no implementation bodies reused.
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/I/IHandlerFunctor.h; MIT.
// IHandlerFunctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IHandlerFunctorRepresentedLayout: GUESS(medium) STANDIN; represented base-object layout.
// The published AnimHandler alias has size 16; template arguments add no object fields.
// Its BSIntrusiveRefCounted base supplies the actual 32-bit reference count at offset 8.
// Explicit pad0C is omitted; compiler alignment supplies the represented trailing space.
// Unassessed virtual methods and concrete-handler definitions are not reconstructed.
// Target leaf code independently writes this base RTTI vtable and deallocates size 16.
// Size/layout agreement alone is not a comparator match or an original owner-definition claim.
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
// Code origin: declarations adapted from the pinned represented community header; no implementation bodies reused.
// IHandlerFunctorBulkLayout, BSIntrusiveRefCountedBulkLayout: GUESS(medium) STANDIN; represented layout aliases.
#pragma once
#include <cstddef>
#include "BSIntrusiveRefCountedBulkLayout.h"
namespace ResearchLayouts {
class IHandlerFunctorBulkLayout : public BSIntrusiveRefCountedBulkLayout {
public:
    virtual ~IHandlerFunctorBulkLayout();
};
static_assert(sizeof(IHandlerFunctorBulkLayout) == 16, "published represented base size");
static_assert(offsetof(IHandlerFunctorBulkLayout, _refCount) == 8, "represented reference count offset");
}
