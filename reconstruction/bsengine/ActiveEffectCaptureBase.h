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
// ActiveEffectCaptureBase: GUESS(medium) STANDIN; public base declaration adapted as an incomplete method set.
class ActiveEffectCaptureBase {
public:
    virtual ~ActiveEffectCaptureBase();
};
static_assert(sizeof(ActiveEffectCaptureBase) == 8, "represented base");
// CaptureLayout5ba920: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5ba920 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5ba920() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout5ba920) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5ba920, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5ba920, capture10) == 16, "observed member offset");
// CaptureLayout5bec70: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5bec70 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5bec70() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 1-byte access at offset 0x18
    std::uint8_t capture18;
};
static_assert(sizeof(CaptureLayout5bec70) == 32, "represented captures");
static_assert(offsetof(CaptureLayout5bec70, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5bec70, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout5bec70, capture18) == 24, "observed member offset");
// CaptureLayout5c67b0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5c67b0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5c67b0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout5c67b0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5c67b0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5c67b0, capture10) == 16, "observed member offset");
// CaptureLayout5d46c0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d46c0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d46c0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
    // capture20: GUESS(low); observed 8-byte access at offset 0x20
    std::uint64_t capture20;
};
static_assert(sizeof(CaptureLayout5d46c0) == 40, "represented captures");
static_assert(offsetof(CaptureLayout5d46c0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d46c0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout5d46c0, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout5d46c0, capture20) == 32, "observed member offset");
// CaptureLayout5d46f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d46f0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d46f0() override;
    // capture08: GUESS(low); observed 1-byte access at offset 0x8
    std::uint8_t capture08;
};
static_assert(sizeof(CaptureLayout5d46f0) == 16, "represented captures");
static_assert(offsetof(CaptureLayout5d46f0, capture08) == 8, "observed member offset");
// CaptureLayout5d4720: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4720 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4720() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 4-byte access at offset 0x10
    std::uint32_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
    // capture20: GUESS(low); observed 8-byte access at offset 0x20
    std::uint64_t capture20;
    // capture28: GUESS(low); observed 8-byte access at offset 0x28
    std::uint64_t capture28;
    // capture30: GUESS(low); observed 4-byte access at offset 0x30
    std::uint32_t capture30;
};
static_assert(sizeof(CaptureLayout5d4720) == 56, "represented captures");
static_assert(offsetof(CaptureLayout5d4720, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d4720, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout5d4720, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout5d4720, capture20) == 32, "observed member offset");
static_assert(offsetof(CaptureLayout5d4720, capture28) == 40, "observed member offset");
static_assert(offsetof(CaptureLayout5d4720, capture30) == 48, "observed member offset");
// CaptureLayout5d4850: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4850 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4850() override;
    // capture08: GUESS(low); observed 1-byte access at offset 0x8
    std::uint8_t capture08;
};
static_assert(sizeof(CaptureLayout5d4850) == 16, "represented captures");
static_assert(offsetof(CaptureLayout5d4850, capture08) == 8, "observed member offset");
// CaptureLayout5d4880: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4880 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4880() override;
    // capture08: GUESS(low); observed 2-byte access at offset 0x8
    std::uint16_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout5d4880) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5d4880, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d4880, capture10) == 16, "observed member offset");
// CaptureLayout5d48f0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d48f0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d48f0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout5d48f0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5d48f0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d48f0, capture10) == 16, "observed member offset");
// CaptureLayout5d4920: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4920 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4920() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout5d4920) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5d4920, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d4920, capture10) == 16, "observed member offset");
// CaptureLayout5d4950: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4950 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4950() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture0C: GUESS(low); observed 1-byte access at offset 0xc
    std::uint8_t capture0C;
};
static_assert(sizeof(CaptureLayout5d4950) == 16, "represented captures");
static_assert(offsetof(CaptureLayout5d4950, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d4950, capture0C) == 12, "observed member offset");
// CaptureLayout5d4980: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d4980 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d4980() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout5d4980) == 24, "represented captures");
static_assert(offsetof(CaptureLayout5d4980, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d4980, capture10) == 16, "observed member offset");
// CaptureLayout5d49b0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d49b0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d49b0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 8-byte access at offset 0x18
    std::uint64_t capture18;
    // capture20: GUESS(low); observed 8-byte access at offset 0x20
    std::uint64_t capture20;
    // capture28: GUESS(low); observed 4-byte access at offset 0x28
    std::uint32_t capture28;
    // capture2C: GUESS(low); observed 1-byte access at offset 0x2c
    std::uint8_t capture2C;
};
static_assert(sizeof(CaptureLayout5d49b0) == 48, "represented captures");
static_assert(offsetof(CaptureLayout5d49b0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d49b0, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout5d49b0, capture18) == 24, "observed member offset");
static_assert(offsetof(CaptureLayout5d49b0, capture20) == 32, "observed member offset");
static_assert(offsetof(CaptureLayout5d49b0, capture28) == 40, "observed member offset");
static_assert(offsetof(CaptureLayout5d49b0, capture2C) == 44, "observed member offset");
// CaptureLayout5d6010: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout5d6010 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout5d6010() override;
    // capture08: GUESS(low); observed 4-byte access at offset 0x8
    std::uint32_t capture08;
    // capture0C: GUESS(low); observed 1-byte access at offset 0xc
    std::uint8_t capture0C;
};
static_assert(sizeof(CaptureLayout5d6010) == 16, "represented captures");
static_assert(offsetof(CaptureLayout5d6010, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout5d6010, capture0C) == 12, "observed member offset");
// CaptureLayout6daab0: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6daab0 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout6daab0() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout6daab0) == 24, "represented captures");
static_assert(offsetof(CaptureLayout6daab0, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6daab0, capture10) == 16, "observed member offset");
// CaptureLayout6dab10: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout6dab10 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout6dab10() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
    // capture18: GUESS(low); observed 1-byte access at offset 0x18
    std::uint8_t capture18;
};
static_assert(sizeof(CaptureLayout6dab10) == 32, "represented captures");
static_assert(offsetof(CaptureLayout6dab10, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout6dab10, capture10) == 16, "observed member offset");
static_assert(offsetof(CaptureLayout6dab10, capture18) == 24, "observed member offset");
// CaptureLayout84db10: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout84db10 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout84db10() override;
    // capture08: GUESS(low); observed 8-byte access at offset 0x8
    std::uint64_t capture08;
    // capture10: GUESS(low); observed 1-byte access at offset 0x10
    std::uint8_t capture10;
};
static_assert(sizeof(CaptureLayout84db10) == 24, "represented captures");
static_assert(offsetof(CaptureLayout84db10, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout84db10, capture10) == 16, "observed member offset");
// CaptureLayout9bb490: GUESS(low) STANDIN; independent owner binding and per-field access evidence retained privately.
class CaptureLayout9bb490 : public ActiveEffectCaptureBase {
public:
    ~CaptureLayout9bb490() override;
    // capture08: GUESS(low); observed 2-byte access at offset 0x8
    std::uint16_t capture08;
    // capture10: GUESS(low); observed 8-byte access at offset 0x10
    std::uint64_t capture10;
};
static_assert(sizeof(CaptureLayout9bb490) == 24, "represented captures");
static_assert(offsetof(CaptureLayout9bb490, capture08) == 8, "observed member offset");
static_assert(offsetof(CaptureLayout9bb490, capture10) == 16, "observed member offset");
}
