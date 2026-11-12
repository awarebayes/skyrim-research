// TESRaceForm::CopyComponent, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1ef750, 63 bytes (CopyComponent).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESRaceForm.h"

void TESRaceForm::CopyComponent(BaseFormComponent* a_rhs)
{
    TESRaceForm* rhs = dynamic_cast<TESRaceForm*>(a_rhs);
    if (rhs) {
        race = rhs->race;
    }
}
