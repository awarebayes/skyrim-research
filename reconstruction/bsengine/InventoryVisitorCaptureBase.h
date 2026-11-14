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
// InventoryVisitorCaptureBase: GUESS(medium) STANDIN; public base declaration adapted as an incomplete method set.
class InventoryVisitorCaptureBase {
public:
    virtual ~InventoryVisitorCaptureBase();
};
static_assert(sizeof(InventoryVisitorCaptureBase) == 8, "represented base");
// CaptureLayout2405c0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout2405c0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout2405c0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
    // capture14: GUESS(low); observed 4-byte access at offset 0x14
    std::uint32_t capture14;
};
static_assert(sizeof(CaptureLayout2405c0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout2405c0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout2405c0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout2405c0, capture14) == 20, "observed member offset");
// CaptureLayout240620: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout240620 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout240620() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout240620) == 24, "represented captures");
static_assert(offsetof(CaptureLayout240620, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout240620, capture10) == 16, "observed member offset");
// CaptureLayout240650: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout240650 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout240650() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
};
static_assert(sizeof(CaptureLayout240650) == 16, "represented captures");
static_assert(offsetof(CaptureLayout240650, capture08) == 8, "observed member offset");
// CaptureLayout2406b0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout2406b0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout2406b0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout2406b0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout2406b0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout2406b0, capture10) == 16, "observed member offset");
// CaptureLayout2406e0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout2406e0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout2406e0() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture0C: GUESS(low); observed 1-byte access at offset 0xc
    std::uint8_t capture0C;
};
static_assert(sizeof(CaptureLayout2406e0) == 16, "represented captures");
static_assert(offsetof(CaptureLayout2406e0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout2406e0, capture0C) == 12, "observed member offset");
// CaptureLayout2407d0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout2407d0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout2407d0() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout2407d0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout2407d0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout2407d0, capture10) == 16, "observed member offset");
// CaptureLayout240800: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout240800 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout240800() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout240800) == 24, "represented captures");
static_assert(offsetof(CaptureLayout240800, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout240800, capture10) == 16, "observed member offset");
// CaptureLayout3cbc30: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout3cbc30 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout3cbc30() override;
    // capture08: GUESS(low); observed 1-byte access at offset 0x8
    std::uint8_t capture08;
};
static_assert(sizeof(CaptureLayout3cbc30) == 16, "represented captures");
static_assert(offsetof(CaptureLayout3cbc30, capture08) == 8, "observed member offset");
// CaptureLayout41e650: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout41e650 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout41e650() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
};
static_assert(sizeof(CaptureLayout41e650) == 16, "represented captures");
static_assert(offsetof(CaptureLayout41e650, capture08) == 8, "observed member offset");
// CaptureLayout5d6040: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d6040 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout5d6040() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
};
static_assert(sizeof(CaptureLayout5d6040) == 16, "represented captures");
static_assert(offsetof(CaptureLayout5d6040, capture08) == 8, "observed member offset");
// CaptureLayout6daba0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6daba0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout6daba0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout6daba0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6daba0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6daba0, capture10) == 16, "observed member offset");
// CaptureLayout6df8f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6df8f0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout6df8f0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
};
static_assert(sizeof(CaptureLayout6df8f0) == 16, "represented captures");
static_assert(offsetof(CaptureLayout6df8f0, capture08) == 8, "observed member offset");
// CaptureLayout735a20: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout735a20 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout735a20() override;
    // capture08: GUESS(low); observed 1-byte access at offset 0x8
    std::uint8_t capture08;
};
static_assert(sizeof(CaptureLayout735a20) == 16, "represented captures");
static_assert(offsetof(CaptureLayout735a20, capture08) == 8, "observed member offset");
// CaptureLayout73ab90: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout73ab90 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout73ab90() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
    // capture14: GUESS(low); observed 4-byte access at offset 0x14
    std::uint32_t capture14;
    // capture18: GUESS(low); observed 4-byte access at offset 0x18
    std::uint32_t capture18;
    // capture1C: GUESS(low); observed 4-byte access at offset 0x1c
    std::uint32_t capture1C;
};
static_assert(sizeof(CaptureLayout73ab90) == 32, "represented captures");
static_assert(offsetof(CaptureLayout73ab90, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout73ab90, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout73ab90, capture14) == 20, "observed member offset");
static_assert(offsetof(CaptureLayout73ab90, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout73ab90, capture1C) == 28, "observed member offset");
// CaptureLayout73ac00: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout73ac00 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout73ac00() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture0C: GUESS(low); observed 4-byte access at offset 0xc
    std::uint32_t capture0C;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
};
static_assert(sizeof(CaptureLayout73ac00) == 24, "represented captures");
static_assert(offsetof(CaptureLayout73ac00, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout73ac00, capture0C) == 12, "observed member offset");
static_assert(offsetof(CaptureLayout73ac00, capture10) == 16, "observed member offset");
// CaptureLayout9426d0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout9426d0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout9426d0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
};
static_assert(sizeof(CaptureLayout9426d0) == 16, "represented captures");
static_assert(offsetof(CaptureLayout9426d0, capture08) == 8, "observed member offset");
// CaptureLayout9bb4c0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout9bb4c0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout9bb4c0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 2-byte access at offset 0x10
    std::uint16_t capture10;
};
static_assert(sizeof(CaptureLayout9bb4c0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout9bb4c0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout9bb4c0, capture10) == 16, "observed member offset");
// CaptureLayout9bb4f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout9bb4f0 : public InventoryVisitorCaptureBase {
public:
    ~CaptureLayout9bb4f0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 2-byte access at offset 0x10
    std::uint16_t capture10;
};
static_assert(sizeof(CaptureLayout9bb4f0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout9bb4f0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout9bb4f0, capture10) == 16, "observed member offset");
}
