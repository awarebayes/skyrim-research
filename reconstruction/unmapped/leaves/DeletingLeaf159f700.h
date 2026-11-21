// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf159f700: GUESS(low)
// 0x159f700 DeletingLeaf159f700::~DeletingLeaf159f700
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf159f700
{
public:
    virtual ~DeletingLeaf159f700() {}
    std::uint8_t unk08[0xA0];  // 08
};
static_assert(sizeof(DeletingLeaf159f700) == 0xA8, "leaf size");
