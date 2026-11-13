// TESObjectBOOK functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-tesobjectbook
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611122314-2).
// Compared functions:
//   RVA 0x27f830, 28 bytes: TESObjectBOOK::InitializeData
//   RVA 0x280540, 77 bytes: TESObjectBOOK::LoadGame
//   RVA 0x2804e0, 85 bytes: TESObjectBOOK::SaveGame
// RVA 0x280210, 121 bytes: TESObjectBOOK::GetActivateText
// Not compared in this unit yet: RVA 0x280760 ~TESObjectBOOK.
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectBOOK.h"

// Not compared: defined so that the compiler emits the vftable (cookbook rule 14).
TESObjectBOOK::TESObjectBOOK()
{
}

// RVA 0x27f830, 28 bytes
void TESObjectBOOK::InitializeData()
{
    data = 0;
    teaches = 0;
    inventoryModel = nullptr;
    TESForm::InitializeData();
}

// RVA 0x280540, 77 bytes
void TESObjectBOOK::LoadGame(BGSLoadFormBuffer* a_buf)
{
    TESForm::LoadGame(a_buf);
    LoadBaseSubobject(unk88, a_buf);
    if ((a_buf->changeFlags & 0x60) != 0) {
        a_buf->LoadDataEndian(&data, 1, 1);
    }
}

// RVA 0x2804e0, 85 bytes
void TESObjectBOOK::SaveGame(BGSSaveFormBuffer* a_buf)
{
    TESForm::SaveGame(a_buf);
    SaveBaseSubobject(unk88, a_buf);
    if ((a_buf->unk1B & 0x60) != 0) {
        a_buf->SaveDataEndian(&data, 1, 1, 0);
    }
}

// RVA 0x280210, 121 bytes
bool TESObjectBOOK::GetActivateText(TESObjectREFR* a_activator, BSString& a_dst)
{
    const char* verb;
    if ((data & 0x4) == 0 || teaches == 0) {
        verb = g_activateVerbPlain;
    } else {
        verb = a_activator->IsCrimeToActivate() ? g_activateVerbSteal : g_activateVerbTake;
    }
    const char* displayName = a_activator->GetDisplayFullName();
    FormatString(a_dst, "%s\n%s", verb, displayName);
    return true;
}
