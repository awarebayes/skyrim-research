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
// MagicTraversalCaptureBase: GUESS(medium) STANDIN; public base declaration adapted as an incomplete method set.
class MagicTraversalCaptureBase {
public:
    virtual ~MagicTraversalCaptureBase();
    std::uint32_t index;
};
static_assert(sizeof(MagicTraversalCaptureBase) == 16, "represented base");
// CaptureLayout152570: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout152570 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout152570() override;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
};
static_assert(sizeof(CaptureLayout152570) == 32, "represented captures");
static_assert(offsetof(CaptureLayout152570, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout152570, capture18) == 24, "observed member offset");
// CaptureLayout1525d0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout1525d0 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout1525d0() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 4-byte access at offset 0x18
    std::uint32_t capture18;
    // capture1C: GUESS(low); observed 4-byte access at offset 0x1c
    std::uint32_t capture1C;
    // capture20: GUESS(low); observed 1-byte access at offset 0x20
    std::uint8_t capture20;
};
static_assert(sizeof(CaptureLayout1525d0) == 40, "represented captures");
static_assert(offsetof(CaptureLayout1525d0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout1525d0, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout1525d0, capture1C) == 28, "observed member offset");
static_assert(offsetof(CaptureLayout1525d0, capture20) == 32, "observed member offset");
// CaptureLayout152600: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout152600 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout152600() override;
};
static_assert(sizeof(CaptureLayout152600) == 16, "represented captures");
// CaptureLayout152630: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout152630 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout152630() override;
};
static_assert(sizeof(CaptureLayout152630) == 16, "represented captures");
// CaptureLayout1543d0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout1543d0 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout1543d0() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
    // capture20: GUESS(low); observed 8-byte access at offset 0x20
    std::uint64_t capture20;
    // capture28: GUESS(low); observed 1-byte access at offset 0x28
    std::uint8_t capture28;
};
static_assert(sizeof(CaptureLayout1543d0) == 48, "represented captures");
static_assert(offsetof(CaptureLayout1543d0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout1543d0, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout1543d0, capture20) == 32, "observed member offset");
static_assert(offsetof(CaptureLayout1543d0, capture28) == 40, "observed member offset");
// CaptureLayout2405f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout2405f0 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout2405f0() override;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
};
static_assert(sizeof(CaptureLayout2405f0) == 32, "represented captures");
static_assert(offsetof(CaptureLayout2405f0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout2405f0, capture18) == 24, "observed member offset");
// CaptureLayout6dab70: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6dab70 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout6dab70() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
};
static_assert(sizeof(CaptureLayout6dab70) == 32, "represented captures");
static_assert(offsetof(CaptureLayout6dab70, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout6dab70, capture18) == 24, "observed member offset");
// CaptureLayout6dac30: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6dac30 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout6dac30() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 1-byte access at offset 0x18
    std::uint8_t capture18;
};
static_assert(sizeof(CaptureLayout6dac30) == 32, "represented captures");
static_assert(offsetof(CaptureLayout6dac30, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout6dac30, capture18) == 24, "observed member offset");
// CaptureLayout6dac60: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6dac60 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout6dac60() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
};
static_assert(sizeof(CaptureLayout6dac60) == 32, "represented captures");
static_assert(offsetof(CaptureLayout6dac60, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout6dac60, capture18) == 24, "observed member offset");
// CaptureLayout804ca0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout804ca0 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout804ca0() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
};
static_assert(sizeof(CaptureLayout804ca0) == 32, "represented captures");
static_assert(offsetof(CaptureLayout804ca0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout804ca0, capture18) == 24, "observed member offset");
// CaptureLayout94a8f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout94a8f0 : public MagicTraversalCaptureBase {
public:
    ~CaptureLayout94a8f0() override;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
    // capture20: GUESS(low); observed 8-byte access at offset 0x20
    std::uint64_t capture20;
    // capture28: GUESS(low); observed 8-byte access at offset 0x28
    std::uint64_t capture28;
    // capture30: GUESS(low); observed 1-byte access at offset 0x30
    std::uint8_t capture30;
};
static_assert(sizeof(CaptureLayout94a8f0) == 56, "represented captures");
static_assert(offsetof(CaptureLayout94a8f0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout94a8f0, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout94a8f0, capture20) == 32, "observed member offset");
static_assert(offsetof(CaptureLayout94a8f0, capture28) == 40, "observed member offset");
static_assert(offsetof(CaptureLayout94a8f0, capture30) == 48, "observed member offset");
}
