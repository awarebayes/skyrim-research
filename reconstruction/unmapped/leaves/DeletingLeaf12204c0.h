// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in reconstructed from the pinned image listing; no external body reused.
// DeletingLeaf12204c0, unknown08, unknown10: GUESS(low) STANDIN
#pragma once
#include <cstdint>
#include <cstddef>

class DeletingLeaf12204c0
{
public:
    DeletingLeaf12204c0();
    virtual ~DeletingLeaf12204c0();  // compared: 0x12204c0
    void* unknown08;
    void* unknown10;
};
static_assert(sizeof(DeletingLeaf12204c0) == 0x18, "size observed from the sized delete argument");
