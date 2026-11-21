// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// Code origin: original stand-in; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf285790, unknown08: GUESS(low) STANDIN
#pragma once

class DeletingLeaf285790
{
public:
    DeletingLeaf285790();
    virtual ~DeletingLeaf285790();  // compared: 0x285790
    unsigned char unknown08[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf285790) == 0x18, "size observed from the sized delete argument");
