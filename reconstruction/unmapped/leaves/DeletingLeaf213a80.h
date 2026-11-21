// Source exposure: binary-analysis and pinned image listing.
// Code origin: original; the empty virtual destructor is inferred from the deleting destructor listing.
// Adapted bodies: none
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// 0x213a80 DeletingLeaf213a80::~DeletingLeaf213a80
// DeletingLeaf213a80, object: GUESS(low) STANDIN
#pragma once

class DeletingLeaf213a80
{
public:
    virtual ~DeletingLeaf213a80() {}

    unsigned char storage[0x10];
};
static_assert(sizeof(DeletingLeaf213a80) == 0x18, "leaf size");
