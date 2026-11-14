// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/N/NiPSysGravityModifier.h; MIT.
// NiPSysGravityModifier: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
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
// NiPSysGravityModifierLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
#include <cstddef>
#include "bsengine/BSFixedStringLayout.h"
#include "netimmerse/NiPSysModifierLayout.h"

namespace ResearchLayouts {
class NiAVObject;
class NiPSysGravityModifierLayout : public NiPSysModifierLayout {
public:
    virtual ~NiPSysGravityModifierLayout();
    NiAVObject* gravityObj;
    NiPoint3Layout gravityAxis;
    float decay;
    float strength;
    std::uint32_t forceType;
    float turbulence;
    float scale;
    bool worldAligned;
};
static_assert(sizeof(NiPSysGravityModifierLayout) == 96, "community represented size");
static_assert(offsetof(NiPSysGravityModifierLayout, gravityObj) == 48, "gravityObj offset");
static_assert(offsetof(NiPSysGravityModifierLayout, gravityAxis) == 56, "gravityAxis offset");
static_assert(offsetof(NiPSysGravityModifierLayout, decay) == 68, "decay offset");
static_assert(offsetof(NiPSysGravityModifierLayout, strength) == 72, "strength offset");
static_assert(offsetof(NiPSysGravityModifierLayout, forceType) == 76, "forceType offset");
static_assert(offsetof(NiPSysGravityModifierLayout, turbulence) == 80, "turbulence offset");
static_assert(offsetof(NiPSysGravityModifierLayout, scale) == 84, "scale offset");
static_assert(offsetof(NiPSysGravityModifierLayout, worldAligned) == 88, "worldAligned offset");
}
