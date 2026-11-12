// BGSLocation::InitializeData and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgslocation
// RVA 0x2984a0, 49 bytes (InitializeData);
// RVA 0x29cd00, 52 bytes (~BGSLocation, the scalar deleting destructor in vftable slot 0);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The destructor is compared.
// InitializeData is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "BGSLocation.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the deleting destructor.
BGSLocation::BGSLocation()
{
}

void BGSLocation::InitializeData()
{
    parentLoc = nullptr;
    musicType = nullptr;
    unreportedCrimeFaction = nullptr;
    worldLocMarker = gNullHandle;
    horseLocMarker = gNullHandle;
    worldLocRadius = 0.0f;
    cleared = false;
    everCleared = false;
    lastChecked = 0;
}
