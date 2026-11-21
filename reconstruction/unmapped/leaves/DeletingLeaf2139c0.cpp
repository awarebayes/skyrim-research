// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original; derived from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// 0x2139c0 DeletingLeaf2139c0::~DeletingLeaf2139c0
// Adapted bodies: none
#include "DeletingLeaf2139c0.h"

void operator delete(void*, unsigned __int64) noexcept;

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
DeletingLeaf2139c0::DeletingLeaf2139c0()
{
}

DeletingLeaf2139c0::~DeletingLeaf2139c0()
{
}
