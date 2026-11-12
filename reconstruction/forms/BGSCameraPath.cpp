// BGSCameraPath::InitializeData and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgscamerapath
// RVA 0x316110, 15 bytes (InitializeData);
// RVA 0x317ce0, 52 bytes (~BGSCameraPath, the scalar deleting destructor in vftable slot 0);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSCameraPath.h"

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
BGSCameraPath::BGSCameraPath()
{
}

void BGSCameraPath::InitializeData()
{
    data = 0;
    parentPath = nullptr;
    prevPath = nullptr;
}
