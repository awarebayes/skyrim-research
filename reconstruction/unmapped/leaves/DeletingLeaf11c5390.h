// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and community declarations only
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf11c5390: GUESS(low)
// storage: GUESS(low) STANDIN; opaque extent reconstructed from the sized delete argument
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf11c5390
{
public:
    DeletingLeaf11c5390();
    virtual ~DeletingLeaf11c5390();  // compared: 0x11c5390

    std::uint8_t storage[0x40];
};
static_assert(sizeof(DeletingLeaf11c5390) == 0x48, "size observed from the sized delete argument");
