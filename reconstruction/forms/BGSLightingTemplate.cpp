// BGSLightingTemplate::InitializeData, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgslightingtemplate
// RVA 0x2955d0, 37 bytes (InitializeData);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSLightingTemplate.h"

#include <cstring>

void BGSLightingTemplate::InitializeData()
{
    std::memset(&data, 0, sizeof(data));
    data.fogClamp = 1.0f;
}
