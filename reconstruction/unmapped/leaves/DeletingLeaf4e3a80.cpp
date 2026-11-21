// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// 0x4e3a80 DeletingLeaf4e3a80::~DeletingLeaf4e3a80
// Adapted bodies: none
#include "DeletingLeaf4e3a80.h"

void operator delete(void*, unsigned __int64) noexcept;

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
DeletingLeaf4e3a80::DeletingLeaf4e3a80() {}

DeletingLeaf4e3a80::~DeletingLeaf4e3a80() {}
