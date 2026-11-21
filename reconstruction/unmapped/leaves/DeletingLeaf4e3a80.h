// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf4e3a80, unknown08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf4e3a80
{
public:
    DeletingLeaf4e3a80();
    virtual ~DeletingLeaf4e3a80();  // compared: 0x4e3a80 (scalar deleting destructor)
    std::uint8_t unknown08[0x18];
};
static_assert(sizeof(DeletingLeaf4e3a80) == 0x20, "size observed from the sized delete argument");
