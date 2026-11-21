// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original reconstruction from the pinned image listing; no adapted bodies
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf14dcbc0: GUESS(low)
// 0x14dcbc0 DeletingLeaf14dcbc0::~DeletingLeaf14dcbc0
// Adapted bodies: none
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf14dcbc0
{
public:
    virtual ~DeletingLeaf14dcbc0() {}
    std::uint8_t unk08[0x20];  // 08
};
static_assert(sizeof(DeletingLeaf14dcbc0) == 0x28, "leaf size");
