// TESBoundObject functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-tesboundobject
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611122314-2).
// Compared functions:
//   RVA 0x6b70f0, 51 bytes: TESBoundObject::SendActorItemEquippedEvent
//   RVA 0x278f90, 104 bytes: TESBoundObject::CalculateDoFavor
// Not compared in this unit (near-miss, see task directory): RVA 0x278e50 Activate, RVA 0x277b10
// LoadObjectBound, RVA 0x278ed0 GetActivateText.
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESBoundObject.h"

// RVA 0x6b70f0, 51 bytes
void TESBoundObject::SendActorItemEquippedEvent(TESObjectREFR* a_actor)
{
    if (a_actor != nullptr && a_actor == g_itemEventFilter) {
        ItemEquippedEvent event{ this, a_actor };
        SendItemEvent(GetItemEventSource(), &event);
    }
}

// RVA 0x278f90, 104 bytes
bool TESBoundObject::CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3)
{
    if (a_arg2 && a_arg3 > 2.0f) {
        NotifyFavorEvent(a_activator->unkF8, a_activator, 4, 0x13, g_playerCharacterSingleton, nullptr, false, false, true, false);
        return false;
    }
    return true;
}

// Retained generated leaf; its byte-match evidence is renewed with this unit.
// IsBoundObject: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
bool TESBoundObject::IsBoundObject() const
{
    return true;
}
