// BGSImpactData::InitializeData, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgsimpactdata
// RVA 0x31d7b0, 62 bytes (InitializeData);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSImpactData.h"

void BGSImpactData::InitializeData()
{
    data.soundLevel = 1;
    data.flags = 0;
    data.resultOverride = 0;
    data.unk16 = 0;
    data.effectDuration = 0.25f;
    data.orient = 2;
    data.angleThreshold = 15.0f;
    data.placementRadius = 16.0f;
    decalTextureSet = nullptr;
    decalTextureSet2 = nullptr;
    sound1 = nullptr;
    sound2 = nullptr;
    hazard = nullptr;
}
