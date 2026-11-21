// Source exposure: mixed (binary analysis and cited public declarations).
// Code origin: original stand-in; its shape comes from the pinned image's listing alone, with no external declaration or body reused.
// Adapted bodies: none
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf3b0760: GUESS(low) STANDIN
// unknown08: GUESS(low) STANDIN
#pragma once

class DeletingLeaf3b0760
{
public:
    DeletingLeaf3b0760();
    virtual ~DeletingLeaf3b0760();  // compared: 0x3b0760 (scalar deleting destructor)
    unsigned char unknown08[0x18];
};
static_assert(sizeof(DeletingLeaf3b0760) == 0x20, "size observed from the sized delete argument");
