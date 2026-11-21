// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in; shape and size read from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf4aa130: GUESS(low) STANDIN
// unknown08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf4aa130
{
public:
    DeletingLeaf4aa130();
    virtual ~DeletingLeaf4aa130();  // compared: 0x4aa130
    unsigned char unknown08[0x18];  // 08
};
static_assert(sizeof(DeletingLeaf4aa130) == 0x20, "size observed from the sized delete argument");
