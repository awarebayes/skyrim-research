// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original reconstruction from binary analysis; no external implementation code copied.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf51c480: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf51c480
{
public:
    DeletingLeaf51c480();
    virtual ~DeletingLeaf51c480();  // compared: 0x51c480

    // padding: GUESS(low); storage to the allocation size the deleting destructor frees
    std::uint8_t padding[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf51c480) == 0x18, "deleting leaf size");
