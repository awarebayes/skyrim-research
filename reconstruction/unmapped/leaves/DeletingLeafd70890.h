// Source exposure: binary-analysis and pinned image listing.
// Code origin: original; the empty virtual destructor is inferred from the deleting destructor listing.
// Adapted bodies: none
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// 0xd70890 DeletingLeafd70890::~DeletingLeafd70890
// DeletingLeafd70890, object: GUESS(low) STANDIN
#pragma once

class DeletingLeafd70890
{
public:
    virtual ~DeletingLeafd70890() {}

    unsigned char storage[40];
};
static_assert(sizeof(DeletingLeafd70890) == 0x30, "leaf size");
