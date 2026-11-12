// TESAttackDamageForm: GetAttackDamage, InitializeDataComponent and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s04-baseformcomponent-tesattackdamageform
// RVA 0x1df130, 5 bytes (GetAttackDamage);
// RVA 0x1df0c0, 7 bytes (InitializeDataComponent);
// RVA 0x1df1a0, 43 bytes (~TESAttackDamageForm, the deleting destructor);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "TESAttackDamageForm.h"

TESAttackDamageForm::TESAttackDamageForm()
{
}

TESAttackDamageForm::~TESAttackDamageForm()
{
}

std::uint16_t TESAttackDamageForm::GetAttackDamage() const
{
    return attackDamage;
}

void TESAttackDamageForm::InitializeDataComponent()
{
    attackDamage = 0;
}
