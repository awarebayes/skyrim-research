// TESWeightForm::CopyComponent, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1f3760, 61 bytes (CopyComponent).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESWeightForm.h"

void TESWeightForm::CopyComponent(BaseFormComponent* a_rhs)
{
    TESWeightForm* rhs = dynamic_cast<TESWeightForm*>(a_rhs);
    if (rhs) {
        weight = rhs->weight;
    }
}
