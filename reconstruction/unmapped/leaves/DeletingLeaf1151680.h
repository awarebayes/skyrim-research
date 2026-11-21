// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf1151680: GUESS(low) STANDIN
// hkgpMeshInternals__RayCaster__dtor: CRASHLOGGER_PDB(59818@2026.10.24)
// unknown08: GUESS(low) STANDIN; padding to the size in the sized delete
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf1151680
{
public:
    DeletingLeaf1151680();
    virtual ~DeletingLeaf1151680();  // compared: 0x1151680
    unsigned char unknown08[56];
};
static_assert(sizeof(DeletingLeaf1151680) == 0x40, "size observed from the sized delete argument");
