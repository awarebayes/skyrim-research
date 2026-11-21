// Source exposure: binary-analysis and pinned image listing.
// Code origin: original; the empty virtual destructor is inferred from the deleting destructor listing.
// Adapted bodies: none
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// 0xd709e0 DeletingLeafd709e0::~DeletingLeafd709e0
// DeletingLeafd709e0, object: GUESS(low) STANDIN
#pragma once

class DeletingLeafd709e0
{
public:
    virtual ~DeletingLeafd709e0() {}

    unsigned char storage[64];
};
static_assert(sizeof(DeletingLeafd709e0) == 0x48, "leaf size");
