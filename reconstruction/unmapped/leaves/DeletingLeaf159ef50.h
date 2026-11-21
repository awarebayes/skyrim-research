// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf159ef50: GUESS(low)
// 0x159ef50 DeletingLeaf159ef50::~DeletingLeaf159ef50
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf159ef50
{
public:
    virtual ~DeletingLeaf159ef50() {}
    std::uint8_t unk08[0x18];  // 08
};
static_assert(sizeof(DeletingLeaf159ef50) == 0x20, "leaf size");
