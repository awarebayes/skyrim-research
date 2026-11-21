// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; derived from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf2139c0: GUESS(low); the sized delete argument is 0x18
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf2139c0
{
public:
    DeletingLeaf2139c0();
    virtual ~DeletingLeaf2139c0();  // compared: 0x2139c0

    std::uint8_t pad[0x10];
};
static_assert(sizeof(DeletingLeaf2139c0) == 0x18, "size");
