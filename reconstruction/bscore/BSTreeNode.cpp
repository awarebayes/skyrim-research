// Source exposure: mixed (community names; the pinned image listing).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original; the pinned image listing and the committed CrashLogger PDB names only
// 0x14e93d0 BSTreeNode::OnVisible
// Adapted bodies: none
// gVisibilityGate, gFadeDelta, gFadeThreshold: GUESS(low)
#include "BSTreeNode.h"

extern bool gVisibilityGate;
extern float gFadeDelta;
extern float gFadeThreshold;

void BSTreeNode::OnVisible(NiCullingProcess* a_process, int a_arg)
{
    if (a_process->unk121 != 0 && gVisibilityGate) {
        if (unkEC - gFadeDelta > gFadeThreshold) {
            return;
        }
    }
    BSLeafAnimNode::OnVisible(a_process, a_arg);
    NodeAt180* node = unk180;
    if (node != nullptr && node->unk12C > 0) {
        unk153 &= 0xAF;
        unk153 |= 0x20;
        unk14C = 0.0f;
    }
}
