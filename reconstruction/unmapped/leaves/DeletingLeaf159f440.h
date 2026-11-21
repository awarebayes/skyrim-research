// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf159f440: GUESS(low)
// 0x159f440 DeletingLeaf159f440::~DeletingLeaf159f440
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf159f440
{
public:
    virtual ~DeletingLeaf159f440() {}
    std::uint8_t unk08[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf159f440) == 0x18, "leaf size");
