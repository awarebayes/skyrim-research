// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// Code origin: original stand-in; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// 0x285790 DeletingLeaf285790::~DeletingLeaf285790
// Adapted bodies: none
#include "DeletingLeaf285790.h"

// The complete destructor is empty and inlines into the deleting destructor, which the target
// emits without a separate call. Defining the constructor makes the compiler emit the vftable.
DeletingLeaf285790::DeletingLeaf285790() {}

DeletingLeaf285790::~DeletingLeaf285790() {}
