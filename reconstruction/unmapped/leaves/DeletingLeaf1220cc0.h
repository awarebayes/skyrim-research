// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in reconstructed from the pinned image listing; no external body reused.
// DeletingLeaf1220cc0, unknown08, unknown10: GUESS(low) STANDIN
#pragma once
#include <cstdint>
#include <cstddef>

class DeletingLeaf1220cc0
{
public:
    DeletingLeaf1220cc0();
    virtual ~DeletingLeaf1220cc0();  // compared: 0x1220cc0
    void* unknown08;
    void* unknown10;
};
static_assert(sizeof(DeletingLeaf1220cc0) == 0x18, "size observed from the sized delete argument");
