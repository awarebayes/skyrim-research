// TESImageSpaceModifier editor ID accessors and destructor, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x2a8e30, 22 bytes (GetFormEditorID).
// RVA 0x2a8e70, 26 bytes (SetFormEditorID).
// RVA 0x2a8df0, 52 bytes (scalar deleting destructor of TESImageSpaceModifier).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. SetFormEditorID and the destructor are compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "TESImageSpaceModifier.h"

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
TESImageSpaceModifier::TESImageSpaceModifier()
{
}

const char* TESImageSpaceModifier::GetFormEditorID() const
{
    return formEditorID.c_str();
}

bool TESImageSpaceModifier::SetFormEditorID(const char* a_str)
{
    formEditorID.Set(a_str, 0);
    return true;
}
