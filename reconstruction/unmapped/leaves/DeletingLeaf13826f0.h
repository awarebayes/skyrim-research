// Source exposure: binary-analysis of the pinned image listing.
// Code origin: original; minimal stand-in naming from the generated leaf family.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf13826f0, object, unk08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf13826f0
{
public:
    virtual ~DeletingLeaf13826f0() {}
    std::uint8_t unk08[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf13826f0) == 0x18, "image size");
