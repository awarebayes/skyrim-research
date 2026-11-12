// TESObjectLAND::CreateDuplicateForm and SetAltered, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x2a9130, 48 bytes (CreateDuplicateForm).
// RVA 0x2aa2e0, 56 bytes (SetAltered).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESObjectLAND.h"

TESForm* TESObjectLAND::CreateDuplicateForm(bool a_createEditorID, void* a_arg2)
{
    (void)a_createEditorID;
    return dynamic_cast<TESObjectLAND*>(TESForm::CreateDuplicateForm(false, a_arg2));
}

void TESObjectLAND::SetAltered(bool a_set)
{
    TESForm::SetAltered(a_set);
    if (a_set && parentCell) {
        parentCell->SetAltered(true);
    }
}
