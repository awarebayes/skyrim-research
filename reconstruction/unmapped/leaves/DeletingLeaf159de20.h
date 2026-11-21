// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf159de20: GUESS(low)
// 0x159de20 DeletingLeaf159de20::~DeletingLeaf159de20
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf159de20
{
public:
    virtual ~DeletingLeaf159de20() {}
    std::uint8_t unk08[0x98];  // 08
};
static_assert(sizeof(DeletingLeaf159de20) == 0xA0, "leaf size");
