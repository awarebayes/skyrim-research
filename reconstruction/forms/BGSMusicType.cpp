// BGSMusicType::GetFormEditorID, SetFormEditorID, DoPause and the destructor adjustor thunk, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgsmusictype
// RVA 0x328688, 9 bytes (dtor, the vtable thunk of the BSIMusicType base at +0x20 into the deleting destructor);
// RVA 0x328550, 19 bytes (GetFormEditorID);
// RVA 0x328570, 20 bytes (SetFormEditorID);
// RVA 0x327e40, 39 bytes (DoPause);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above other than GetFormEditorID are compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "BGSMusicType.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the destructor thunk.
BGSMusicType::BGSMusicType()
{
}

BGSMusicType::~BGSMusicType()
{
}

const char* BGSMusicType::GetFormEditorID() const
{
    return formEditorID.c_str();
}

bool BGSMusicType::SetFormEditorID(const char* a_str)
{
    formEditorID = a_str;
    return true;
}

void BGSMusicType::DoPause()
{
    tracks[currentTrackIndex]->DoPause();
    typeStatus = 2;
}
