// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf1193080: GUESS(low) STANDIN
// unknown08: GUESS(low) STANDIN; padding to the size in the sized delete
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf1193080
{
public:
    DeletingLeaf1193080();
    virtual ~DeletingLeaf1193080();  // compared: 0x1193080
    unsigned char unknown08[0x130];
};
static_assert(sizeof(DeletingLeaf1193080) == 0x138, "size observed from the sized delete argument");
