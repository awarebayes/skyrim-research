// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf11c5330: GUESS(low) STANDIN
// _anonymous_namespace___CheckSphereVisitor__dtor: CRASHLOGGER_PDB(59818@2026.10.24)
// unknown08: GUESS(low) STANDIN; padding to the size in the sized delete
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf11c5330
{
public:
    DeletingLeaf11c5330();
    virtual ~DeletingLeaf11c5330();  // compared: 0x11c5330
    unsigned char unknown08[0x18];
};
static_assert(sizeof(DeletingLeaf11c5330) == 0x20, "size observed from the sized delete argument");
