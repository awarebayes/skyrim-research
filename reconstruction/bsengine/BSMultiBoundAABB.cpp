// BSMultiBoundAABB functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsmultiboundaabb
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611122349-2), starting from a tools/skeleton.py skeleton.
// Compared functions in this file:
//   RVA 0x213ab0, 50 bytes: BSMultiBoundAABB::~BSMultiBoundAABB
//   RVA 0xfce870, 55 bytes: BSMultiBoundAABB::LoadBinary
// Not in this file (not matched, kept in the unit's near-miss/ folder): RVA 0x213c70 GetLength,
// 0xfcf150 Unk_2B, 0xfcf1a0 GetWithinPoint, 0xfcf0a0 Unk_2A, 0xfceba0 Unk_28.
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
#include "BSMultiBoundAABB.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSMultiBoundAABB::BSMultiBoundAABB()
{
}

// Body done: RVA 0x213ab0, 50 bytes, BSMultiBoundAABB::~BSMultiBoundAABB; compared as the scalar
// deleting destructor. The target does the NiRefObject cleanup itself, so keep this empty
// definition and the constructor: the inline base destructors in the header make the compiler
// produce the same body.
BSMultiBoundAABB::~BSMultiBoundAABB()
{
}

// Body done: RVA 0xfce870, 55 bytes, BSMultiBoundAABB::LoadBinary.
void BSMultiBoundAABB::LoadBinary(NiStream& a_stream)
{
    NiObject::LoadBinary(a_stream);
    unk1C.LoadTriple(a_stream);
    unk2C.LoadTriple(a_stream);
}

// Retained generated leaf; its byte-match evidence is renewed with this unit.
// GetType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
std::uint32_t BSMultiBoundAABB::GetType() const
{
    return 0x1;
}
