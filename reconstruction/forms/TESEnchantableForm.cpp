// TESEnchantableForm accessors, InitializeDataComponent and the deleting destructor, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1e20d0, 5 bytes (GetCastingType); RVA 0x1e1e60, 14 bytes (InitializeDataComponent);
// RVA 0x1e20a0, 43 bytes (~TESEnchantableForm, the deleting destructor).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// The constructor is not compared: it is defined so that this unit emits the vftable and with
// it the deleting destructor. Its body is a minimal stand-in.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESEnchantableForm.h"

TESEnchantableForm::TESEnchantableForm()
{
}

TESEnchantableForm::~TESEnchantableForm()
{
}

std::uint16_t TESEnchantableForm::GetCastingType() const
{
    return castingType;
}

void TESEnchantableForm::InitializeDataComponent()
{
    castingType = 3;
    amountofEnchantment = 0;
    formEnchanting = nullptr;
}
