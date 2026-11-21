// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf1184f70: GUESS(low) STANDIN
// unknown08: GUESS(low) STANDIN; padding to the size in the sized delete
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf1184f70
{
public:
    DeletingLeaf1184f70();
    virtual ~DeletingLeaf1184f70();  // compared: 0x1184f70
    unsigned char unknown08[0x350];
};
static_assert(sizeof(DeletingLeaf1184f70) == 0x358, "size observed from the sized delete argument");
