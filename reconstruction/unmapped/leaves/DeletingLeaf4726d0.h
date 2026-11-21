// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and community declarations only
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf4726d0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

// operator delete: the sized form the compared deleting destructor calls
void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf4726d0
{
public:
    DeletingLeaf4726d0();
    virtual ~DeletingLeaf4726d0();  // compared: 0x4726d0

    // pad: GUESS(low); storage sized to the allocation the compared destructor frees
    std::uint8_t pad[0x20];  // 08
};
static_assert(sizeof(DeletingLeaf4726d0) == 0x28, "DeletingLeaf4726d0 size");
