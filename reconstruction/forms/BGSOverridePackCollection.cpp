// BGSOverridePackCollection: InitializeDataComponent and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s04-baseformcomponent-bgsoverridepackcollection
// RVA 0x1daad0, 19 bytes (InitializeDataComponent);
// RVA 0x1db070, 43 bytes (~BGSOverridePackCollection, the deleting destructor);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSOverridePackCollection.h"

BGSOverridePackCollection::BGSOverridePackCollection()
{
}

BGSOverridePackCollection::~BGSOverridePackCollection()
{
}

void BGSOverridePackCollection::InitializeDataComponent()
{
    spectatorOverRidePackList = nullptr;
    observeCorpseOverRidePackList = nullptr;
    guardWarnOverRidePackList = nullptr;
    enterCombatOverRidePackList = nullptr;
}

// BGSOverridePackCollection::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void BGSOverridePackCollection::ClearDataComponent()
{
}
