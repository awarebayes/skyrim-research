// BGSCameraShot::InitializeData and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgscamerashot
// RVA 0x318c10, 44 bytes (InitializeData);
// RVA 0x31a0c0, 52 bytes (~BGSCameraShot, the scalar deleting destructor in vftable slot 0);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSCameraShot.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the deleting destructor.
BGSCameraShot::BGSCameraShot()
{
}

void BGSCameraShot::InitializeData()
{
    data.cameraAction = 2;
    data.playerTimeMult = 0.0f;
    data.targetTimeMult = 0.0f;
    data.maxTime = 0.0f;
    data.minTime = 0.0f;
    data.targetPercentBetweenActors = 0.0f;
    data.nearTargetDistance = 0.0f;
    data.location = 2;
    data.target = 0;
    data.globalTimeMult = 1.0f;
    data.flags = 3;
}
