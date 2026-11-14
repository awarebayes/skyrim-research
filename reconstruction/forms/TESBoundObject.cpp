// TESBoundObject functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-tesboundobject
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 and gpt-6.1-terra from the assigned packs.
// Compared functions:
//   RVA 0x1d21c0, 33 bytes: TESBoundObject::GetBipedObjectForm
//   RVA 0x277b10, 150 bytes: TESBoundObject::LoadObjectBound
//   RVA 0x6b70f0, 51 bytes: TESBoundObject::SendActorItemEquippedEvent
//   RVA 0x278f90, 104 bytes: TESBoundObject::CalculateDoFavor
//   RVA 0x1468a0, 3 bytes: TESBoundObject::IsBoundObject
// Not compared here: Activate and GetActivateText; their near-misses stay in the task directory.
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

#include <intrin.h>
// LoadObjectBound, mod, words: GUESS(low)
void TESBoundObject::LoadObjectBound(TESFile* mod)
{
    if (!mod) return;
    if (mod->GetCurrentSubRecordType() == 0x444e424f) {
        auto words = reinterpret_cast<std::uint16_t*>(reinterpret_cast<std::uint8_t*>(this) + 0x20);
        mod->ReadData(words, 12);
        if (mod->swap) {
            // Each word follows the file byte order flag.
            words[3] = _byteswap_ushort(words[3]);  // File byte order conversion.
            words[4] = _byteswap_ushort(words[4]);  // File byte order conversion.
            words[5] = _byteswap_ushort(words[5]);  // File byte order conversion.
            words[0] = _byteswap_ushort(words[0]);  // File byte order conversion.
            words[1] = _byteswap_ushort(words[1]);  // File byte order conversion.
            words[2] = _byteswap_ushort(words[2]);  // File byte order conversion.
        }
    }
}


// GetBipedObjectForm: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// type: GUESS(low); discriminator read through the shared form layout.
void* TESBoundObject::GetBipedObjectForm()
{
    if (this == nullptr) {
        return nullptr;
    }
    std::uint8_t type = static_cast<std::uint8_t>(formType);
    if (type != 0x1A) {
        if (type != 0x66) {
            return nullptr;
        }
        return reinterpret_cast<std::uint8_t*>(this) + 0x30;
    }
    return reinterpret_cast<std::uint8_t*>(this) + 0x1B0;
}

// Strong-tier additions drafted by gpt-6.1-sol; adapted bodies: none.
// actor: GUESS(low); runtime-checked actor view
bool TESBoundObject::Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t a_targetCount)
{
    ActorActivateView* actor = CastReferenceToActor(a_activatorRef, 0, &g_referenceType, &g_actorType, 0);
    if (actor && a_targetRef) {
        actor->ActivateTarget(a_targetRef, a_targetCount, a_arg3, true);
        return true;
    }
    return false;
}

