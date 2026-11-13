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

// TestBit: GUESS(low); the same by-value bit test as TESObjectREFR.h, kept file-local so this unit does not pull that header in
static inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); skips the work once the form's flag bit 3 is set
void BGSCameraShot::InitItemImpl()
{
    if (TestBit(formFlags, 3)) {
        return;
    }
    ResetImageSpaceModifier(static_cast<TESImageSpaceModifiableForm*>(this), this);
    if (data.globalTimeMult < 0.0001f) {
        data.globalTimeMult = 0.1f;
    }
    SetInitialized(true);
}
