// Build: sse-steam-1-7-104
// Source exposure: community-headers
// Drafted by GPT-6.1 Sol; p106 value layouts adapted from pinned community declarations.
// Labels: v2
// BSFixedString, BSFixedStringCS, Color, NiPoint2, NiPoint3, NiColor, NiColorA,
// NiPointer, BSTSmartPointer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a
// Corresponding named headers under include/RE; data declarations only, no method bodies.
// entry, value: GUESS(medium)
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
// BSFixedStringCSLayout, BSFixedStringLayout, BSTSmartPointerLayout, ColorLayout, CombatInventoryItemSlotLayout, NiColorALayout, NiColorLayout, NiPoint2Layout, NiPoint3Layout, NiPointerLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
namespace ResearchLayouts {
class BGSEquipSlot;
struct CombatInventoryItemSlotLayout { BGSEquipSlot* equipSlot; std::uint32_t slot; };
static_assert(sizeof(CombatInventoryItemSlotLayout) == 16, "value representation");
struct BSFixedStringLayout { const char* entry; };
static_assert(sizeof(BSFixedStringLayout) == 8, "value representation");
struct BSFixedStringCSLayout { const char* entry; };
static_assert(sizeof(BSFixedStringCSLayout) == 8, "value representation");
struct ColorLayout { std::uint8_t red; std::uint8_t green; std::uint8_t blue; std::uint8_t alpha; };
static_assert(sizeof(ColorLayout) == 4, "value representation");
struct NiPoint2Layout { float x; float y; };
static_assert(sizeof(NiPoint2Layout) == 8, "value representation");
struct NiPoint3Layout { float x; float y; float z; };
static_assert(sizeof(NiPoint3Layout) == 12, "value representation");
struct NiColorLayout { float red; float green; float blue; };
static_assert(sizeof(NiColorLayout) == 12, "value representation");
struct NiColorALayout { float red; float green; float blue; float alpha; };
static_assert(sizeof(NiColorALayout) == 16, "value representation");
template<class T> struct NiPointerLayout { T* value; };
template<class T> struct BSTSmartPointerLayout { T* value; };
}
