// BGSMaterialObject::EnsureLoaded and the destructor adjustor thunk, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgsmaterialobject
// RVA 0x321c34, 9 bytes (dtor, the vtable thunk of the BSMaterialObject base at +0x48 into the deleting destructor);
// RVA 0x321740, 22 bytes (EnsureLoaded);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSMaterialObject.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the destructor thunk.
BGSMaterialObject::BGSMaterialObject()
{
}

BGSMaterialObject::~BGSMaterialObject()
{
}

void BGSMaterialObject::EnsureLoaded()
{
    if (properties.empty() && !fileData.empty()) {
        LoadFileData();
    }
}
