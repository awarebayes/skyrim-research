// BGSHeadPart::GetFormEditorID and SetFormEditorID, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgsheadpart
// RVA 0x391020, 22 bytes (GetFormEditorID);
// RVA 0x391210, 23 bytes (SetFormEditorID);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. SetFormEditorID is compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "BGSHeadPart.h"

const char* BGSHeadPart::GetFormEditorID() const
{
    return formEditorID.c_str();
}

bool BGSHeadPart::SetFormEditorID(const char* a_str)
{
    formEditorID = a_str;
    return true;
}
