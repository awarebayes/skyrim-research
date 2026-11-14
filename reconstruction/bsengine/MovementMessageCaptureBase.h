// Build: sse-steam-1-7-104
// Source exposure: mixed (public base declarations and local member-access analysis).
// Drafted by GPT-6.1 Sol; p104b represented scalar captures.
// Labels: v2
// Code origin: base declarations adapted from CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a; derived declarations originally inferred from local field accesses. No implementation bodies reused.
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a (MIT).
// Base source paths: include/RE/I/InventoryChanges.h, M/MagicTarget.h, M/MagicItemTraversalFunctor.h, I/IMessageBoxCallback.h.
// Layout aliases and capture fields: GUESS(low) STANDIN; observed access widths and offsets constrain scalar representations, not original field boundaries or semantic types.
// Only selected deleting code is reconstructed; omitted methods and concrete class definitions are not claimed.
// No array or alignment field is used to force allocation size. Each derived scalar has an observed member access; ordinary compiler alignment supplies gaps.
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
// MovementMessageCaptureBase: GUESS(medium) STANDIN; local RTTI interface with no observed base data.
class MovementMessageCaptureBase {
public:
    virtual ~MovementMessageCaptureBase();
};
static_assert(sizeof(MovementMessageCaptureBase) == 8, "represented base");
// CaptureLayout6bc240: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc240 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc240() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc240) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc240, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc240, capture10) == 16, "observed member offset");
// CaptureLayout6bc270: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc270 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc270() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc270) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc270, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc270, capture10) == 16, "observed member offset");
// CaptureLayout6bc2a0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc2a0 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc2a0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc2a0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc2a0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc2a0, capture10) == 16, "observed member offset");
// CaptureLayout6bc2d0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc2d0 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc2d0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc2d0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc2d0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc2d0, capture10) == 16, "observed member offset");
// CaptureLayout6bc300: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc300 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc300() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc300) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc300, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc300, capture10) == 16, "observed member offset");
// CaptureLayout6bc330: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc330 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc330() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc330) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc330, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc330, capture10) == 16, "observed member offset");
// CaptureLayout6bc360: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc360 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc360() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc360) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc360, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc360, capture10) == 16, "observed member offset");
// CaptureLayout6bc390: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc390 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc390() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc390) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc390, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc390, capture10) == 16, "observed member offset");
// CaptureLayout6bc3c0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc3c0 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc3c0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc3c0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc3c0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc3c0, capture10) == 16, "observed member offset");
// CaptureLayout6bc3f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc3f0 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc3f0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc3f0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc3f0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc3f0, capture10) == 16, "observed member offset");
// CaptureLayout6bc420: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc420 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc420() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc420) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc420, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc420, capture10) == 16, "observed member offset");
// CaptureLayout6bc450: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc450 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc450() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc450) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc450, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc450, capture10) == 16, "observed member offset");
// CaptureLayout6bc480: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc480 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc480() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc480) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc480, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc480, capture10) == 16, "observed member offset");
// CaptureLayout6bc4b0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6bc4b0 : public MovementMessageCaptureBase {
public:
    ~CaptureLayout6bc4b0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout6bc4b0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6bc4b0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6bc4b0, capture10) == 16, "observed member offset");
}
