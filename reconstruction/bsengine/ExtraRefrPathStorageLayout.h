// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/E/ExtraRefrPath.h; MIT.
// ExtraRefrPath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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
// ExtraRefrPathLayout: GUESS(medium) STANDIN; represented layout type names
// Adapted from published p106 represented declaration reconstruction/bsengine/ExtraRefrPathLayout.h.
// Include spelling and local type names changed; all represented fields, bases, size and offset assertions retained.
// ExtraRefrPathStorageLayout: GUESS(medium) STANDIN; compilation-local represented type aliases.
#pragma once
#include <cstdint>
#include <cstddef>
#include "BSExtraDataStorageLayout.h"
#include "BSFixedStringStorageLayout.h"

namespace ResearchLayouts {
class ExtraRefrPathStorageLayout : public BSExtraDataStorageLayout {
public:
    virtual ~ExtraRefrPathStorageLayout();
    NiPoint3StorageLayout startPos;
    NiPoint3StorageLayout startTangent;
    NiPoint3StorageLayout startEuler;
    NiPoint3StorageLayout goalPos;
    NiPoint3StorageLayout goalTangent;
    NiPoint3StorageLayout goalEuler;
    float speed;
    float maxRotSpeed;
    float currentParameter;
    std::uint32_t type;
};
static_assert(sizeof(ExtraRefrPathStorageLayout) == 104, "community represented size");
static_assert(offsetof(ExtraRefrPathStorageLayout, startPos) == 16, "startPos offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, startTangent) == 28, "startTangent offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, startEuler) == 40, "startEuler offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, goalPos) == 52, "goalPos offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, goalTangent) == 64, "goalTangent offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, goalEuler) == 76, "goalEuler offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, speed) == 88, "speed offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, maxRotSpeed) == 92, "maxRotSpeed offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, currentParameter) == 96, "currentParameter offset");
static_assert(offsetof(ExtraRefrPathStorageLayout, type) == 100, "type offset");
}
