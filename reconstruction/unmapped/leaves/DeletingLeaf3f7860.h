// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the pinned image listing and community declarations only.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf3f7860: GUESS(low)
// unk08: GUESS(low); padding to the image's class size of 0x28.
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf3f7860
{
public:
    DeletingLeaf3f7860();
    virtual ~DeletingLeaf3f7860();  // compared: 0x3f7860

    std::uint8_t unk08[0x20];  // 08
};
static_assert(sizeof(DeletingLeaf3f7860) == 0x28, "size");
