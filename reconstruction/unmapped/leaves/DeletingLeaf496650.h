// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original reconstruction from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf496650: GUESS(low)
// pad: GUESS(low); storage to reach the measured 0x18 class size
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf496650
{
public:
    DeletingLeaf496650();
    virtual ~DeletingLeaf496650();  // compared: 0x496650

private:
    std::uint8_t pad[0x10];
};
static_assert(sizeof(DeletingLeaf496650) == 0x18, "layout");
