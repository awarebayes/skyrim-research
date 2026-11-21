// Source exposure: mixed (binary-analysis of the pinned image; minimal stand-in).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in from the pinned image listing; no external body reused.
// DeletingLeaf11392f0: GUESS(low) STANDIN
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf11392f0
{
public:
    virtual ~DeletingLeaf11392f0() {}

private:
    // Unknown storage named by offset; only the 0x30 object size is evidenced.
    std::uint64_t unk8;   // 08
    std::uint64_t unk10;  // 10
    std::uint64_t unk18;  // 18
    std::uint64_t unk20;  // 20
    std::uint64_t unk28;  // 28
};

static_assert(sizeof(DeletingLeaf11392f0) == 0x30, "object size differs from the compared delete");
