// Source exposure: binary-analysis and pinned image listing.
// Code origin: original; the empty virtual destructor is inferred from the deleting destructor listing.
// Adapted bodies: none
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// 0xd70930 DeletingLeafd70930::~DeletingLeafd70930
// DeletingLeafd70930, object: GUESS(low) STANDIN
#pragma once

class DeletingLeafd70930
{
public:
    virtual ~DeletingLeafd70930() {}

    unsigned char storage[16];
};
static_assert(sizeof(DeletingLeafd70930) == 0x18, "leaf size");
