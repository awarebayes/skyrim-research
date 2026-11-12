// TESIdleForm::~TESIdleForm (deleting destructor), build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x3b8200, 52 bytes (scalar deleting destructor of TESIdleForm).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The function above is compared.
#include "TESIdleForm.h"

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
TESIdleForm::TESIdleForm()
{
}
