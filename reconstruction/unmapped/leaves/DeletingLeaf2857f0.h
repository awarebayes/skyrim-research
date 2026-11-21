// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and the generated deleting-leaf pattern
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf2857f0: GUESS(low) STANDIN
// unknown08: GUESS(low); pads the stand-in to the size the target passes to operator delete
#pragma once

#include <cstdint>
#include <cstddef>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf2857f0
{
public:
    DeletingLeaf2857f0();
    virtual ~DeletingLeaf2857f0();  // compared: 0x2857f0
    unsigned char unknown08[0x18];
};
static_assert(sizeof(DeletingLeaf2857f0) == 0x20, "stand-in size");
