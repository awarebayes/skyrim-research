// TESGlobal::GetFormEditorID and SetFormEditorID, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x340be0, 19 bytes (GetFormEditorID).
// RVA 0x340c00, 23 bytes (SetFormEditorID).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. SetFormEditorID is compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "TESGlobal.h"

const char* TESGlobal::GetFormEditorID() const
{
    return formEditorID.c_str();
}

bool TESGlobal::SetFormEditorID(const char* a_str)
{
    formEditorID.Set(a_str, 0);
    return true;
}
