// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original reconstruction; layout and body written from the listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf4088d0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf4088d0
{
public:
    DeletingLeaf4088d0();
    virtual ~DeletingLeaf4088d0() {}  // compared: 0x4088d0 (scalar deleting destructor)

    std::uint8_t padding[0x18];  // 08
};
static_assert(sizeof(DeletingLeaf4088d0) == 0x20, "DeletingLeaf4088d0 size");
