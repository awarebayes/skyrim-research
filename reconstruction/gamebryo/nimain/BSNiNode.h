// Source exposure: mixed (community declarations and the contributor-owned pack).
// Code origin: declarations from community headers; layout from the pinned image listing.
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Base form: shared header declarations/NiNode.h for NiNode.
// BSNiNode, BSNiNode::~BSNiNode, BSNiNode::GetRTTI, BSNiNode::CreateClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "declarations/NiNode.h"

class BSNiNode : public NiNode
{
public:
    virtual ~BSNiNode();  // compared: 0x1005450  // slot 00
    const NiRTTI* GetRTTI() const override;  // 02
    NiObject* CreateClone(NiCloningProcess& a_cloning) override;  // 17
    BSNiNode();
};
static_assert(sizeof(BSNiNode) == 0x128, "BSNiNode size");
