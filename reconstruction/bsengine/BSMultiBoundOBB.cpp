// BSMultiBoundOBB functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bsmultiboundobb
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfcf830, 6 bytes: BSMultiBoundOBB::GetType
//   RVA 0xfcf6a0, 43 bytes: BSMultiBoundOBB::SaveBinary
//   RVA 0x213af0, 50 bytes: BSMultiBoundOBB::~BSMultiBoundOBB
//   RVA 0xfcf630, 55 bytes: BSMultiBoundOBB::LoadBinary
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
// Public declaration-source notice (CommonLibSSE-NG b93280e, MIT):
//   MIT License
//
//   Copyright (c) 2018 Ryan-rsm-McKenzie
//
//   Permission is hereby granted, free of charge, to any person obtaining a copy
//   of this software and associated documentation files (the "Software"), to deal
//   in the Software without restriction, including without limitation the rights
//   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//   copies of the Software, and to permit persons to whom the Software is
//   furnished to do so, subject to the following conditions:
//
//   The above copyright notice and this permission notice shall be included in all
//   copies or substantial portions of the Software.
//
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//   SOFTWARE.
//
#include "BSMultiBoundOBB.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSMultiBoundOBB::BSMultiBoundOBB()
{
}

// Compared function: RVA 0xfcf830, 6 bytes, BSMultiBoundOBB::GetType.
std::uint32_t BSMultiBoundOBB::GetType()
{
    return 2;
}

// Compared function: RVA 0xfcf6a0, 43 bytes, BSMultiBoundOBB::SaveBinary.
void BSMultiBoundOBB::SaveBinary(NiStream& a_stream)
{
    BSMultiBoundAABB::SaveBinary(a_stream);
    unknown40.SaveBinary(a_stream);
}

// Body done: RVA 0x213af0, 50 bytes, BSMultiBoundOBB::~BSMultiBoundOBB; compared as the scalar
// deleting destructor. The target does the NiRefObject cleanup itself, so keep this empty
// definition and the constructor: the inline base destructors in the header make the compiler
// produce the same body.
BSMultiBoundOBB::~BSMultiBoundOBB()
{
}

// Compared function: RVA 0xfcf630, 55 bytes, BSMultiBoundOBB::LoadBinary.
void BSMultiBoundOBB::LoadBinary(NiStream& a_stream)
{
    BSMultiBoundAABB::LoadBinary(a_stream);
    unknown40.LoadBinary(a_stream);
    unknown64 = ComputeFlag();
}
