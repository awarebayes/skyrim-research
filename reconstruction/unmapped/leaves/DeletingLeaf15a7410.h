// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf15a7410: GUESS(low)
// 0x15a7410 DeletingLeaf15a7410::~DeletingLeaf15a7410
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf15a7410
{
public:
    virtual ~DeletingLeaf15a7410() {}
    std::uint8_t unk08[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf15a7410) == 0x18, "leaf size");
