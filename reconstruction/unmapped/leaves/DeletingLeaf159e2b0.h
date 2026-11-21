// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf159e2b0: GUESS(low)
// 0x159e2b0 DeletingLeaf159e2b0::~DeletingLeaf159e2b0
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf159e2b0
{
public:
    virtual ~DeletingLeaf159e2b0() {}
    std::uint8_t unk08[0x48];  // 08
};
static_assert(sizeof(DeletingLeaf159e2b0) == 0x50, "leaf size");
