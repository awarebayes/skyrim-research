// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original; the listing of the pinned image and community declarations only
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2-root-includes.json
// 0x1005450 BSNiNode::~BSNiNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Adapted bodies: none
#include "BSNiNode.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSNiNode::BSNiNode()
{
}

BSNiNode::~BSNiNode()
{
}
