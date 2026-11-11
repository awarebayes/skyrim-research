// NiTimeController::ProcessClone, build sse-steam-1-7-104, RVA 0xef8900, 53 bytes.
//
// Evidence: findings/second-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local instruction listing and
// decompiler output of the pinned image, with types from the header beside this file.
// A byte match does not verify the community method name or the original source shape.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Only ProcessClone is compared.
#include "NiTimeController.h"

void NiTimeController::ProcessClone(NiCloningProcess& a_cloning)
{
    NiObject::ProcessClone(a_cloning);
    if (next) {
        next->ProcessClone(a_cloning);
    }
}
