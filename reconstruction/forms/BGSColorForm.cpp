// BGSColorForm::InitializeData, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgscolorform
// RVA 0x31b530, 7 bytes (InitializeData);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The function listed above is compared.
#include "BGSColorForm.h"

void BGSColorForm::InitializeData()
{
    color.value = 0;
    flags = 0;
}
