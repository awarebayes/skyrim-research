// TESProduceForm::InitializeDataComponent and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1ee470, 14 bytes (InitializeDataComponent); RVA 0x1eee40, 43 bytes (~TESProduceForm, the deleting destructor).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// The constructor is not compared: it is defined so that this unit emits the vftable and with
// it the deleting destructor. Its body is a minimal stand-in.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESProduceForm.h"

TESProduceForm::TESProduceForm()
{
}

TESProduceForm::~TESProduceForm()
{
}

void TESProduceForm::InitializeDataComponent()
{
    produceItem = nullptr;
    harvestSound = nullptr;
    for (int i = 0; i < 4; ++i) {
        produceChance[i] = 0;
    }
}

void TESProduceForm::ClearDataComponent()
{
}
