// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/C/CombatInventoryItemMagic.h; MIT.
// CombatInventoryItemMagic: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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
// CombatInventoryItemMagicLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
#include <cstddef>
#include "actors/CombatInventoryItemLayout.h"

namespace ResearchLayouts {
class Effect;
class CombatInventoryItemMagicLayout : public CombatInventoryItemLayout {
public:
    virtual ~CombatInventoryItemMagicLayout();
    float minRange;
    float maxRange;
    float tacticalDuration;
    float power;
    float currentAV;
    Effect* effect;
};
static_assert(sizeof(CombatInventoryItemMagicLayout) == 80, "community represented size");
static_assert(offsetof(CombatInventoryItemMagicLayout, minRange) == 48, "minRange offset");
static_assert(offsetof(CombatInventoryItemMagicLayout, maxRange) == 52, "maxRange offset");
static_assert(offsetof(CombatInventoryItemMagicLayout, tacticalDuration) == 56, "tacticalDuration offset");
static_assert(offsetof(CombatInventoryItemMagicLayout, power) == 60, "power offset");
static_assert(offsetof(CombatInventoryItemMagicLayout, currentAV) == 64, "currentAV offset");
static_assert(offsetof(CombatInventoryItemMagicLayout, effect) == 72, "effect offset");
}
