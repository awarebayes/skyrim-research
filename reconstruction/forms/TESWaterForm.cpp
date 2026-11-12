// TESWaterForm accessor and destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s05-tesform-teswaterform
// RVA 0x306f80, 10 bytes (GetDangerous); RVA 0x3078e0, 52 bytes (~TESWaterForm, the deleting destructor).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// The plain destructor (target 0x306300, its name a low-confidence guess labelled at the declaration) is declared, not defined,
// in this unit and bound by position; the sized operator delete (0x15a743c) is the global one.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its threshold.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Both functions above are compared.
#include "TESWaterForm.h"

// Not compared: defined so that this unit emits the vftable and with it the deleting destructor.
TESWaterForm::TESWaterForm()
{
}

bool TESWaterForm::GetDangerous() const
{
    return flags & 1;
}
