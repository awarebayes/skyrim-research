// TESBoundObject declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-tesboundobject
// Source exposure: mixed (names and declarations from community headers; base classes, offsets and
// the compared functions from the pinned image).
// Base form: shared header ../forms/TESForm.h for TESForm. The brief's other shared headers
// (TESObjectREFR.h, ../actors/Actor.h, TESFile.h) each redefine TESForm or TESObjectREFR, so they
// cannot be included with TESForm.h; header-gap TESObjectREFR, Actor and TESFile.
// TESBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// CalculateDoFavor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GetBipedObjectForm, SendActorItemEquippedEvent: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); the community declarations are unknown, the signatures here come from the listings
// TESObject: STANDIN EXE_RTTI
// Actor, TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the members the compared code reads are declared
// unk00, unkF8: GUESS(low); the offsets are the ones the listings read, the layout around them is not claimed
// ItemEquippedEvent, GetItemEventSource, SendItemEvent, NotifyFavorEvent, g_itemEventFilter: GUESS(low); the image calls or reads them with these arguments, the names are invented
// g_playerCharacterSingleton: GUESS(low); the image reads the PlayerCharacter singleton pointer at 0x3230778
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class TESObjectREFR;
class Actor;
class TESBoundObject;
class PlayerCharacter;

// TESObject: STANDIN EXE_RTTI
class TESObject : public TESForm
{
public:
};

// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only its identity is declared, the compared code passes it through
class TESObjectREFR
{
public:
};

// Actor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the offsets are from the start of the Actor, the field at 0xF8 is read by CalculateDoFavor
class Actor
{
public:
    // unk00: GUESS(low); bytes up to the field CalculateDoFavor reads
    std::uint8_t unk00[0xF8];  // 00
    // unkF8: GUESS(low); a pointer the favor notification receives
    void* unkF8;  // F8
};

// ItemEquippedEvent: GUESS(low); two pointers passed to the equip notification
struct ItemEquippedEvent
{
    TESBoundObject* item;   // 00
    TESObjectREFR*  actor;  // 08
};

// GetItemEventSource, SendItemEvent: GUESS(low); the image calls them with these arguments
void* GetItemEventSource();
void  SendItemEvent(void* a_source, ItemEquippedEvent* a_event);

// NotifyFavorEvent: GUESS(low); the image passes ten arguments, four in registers and six on the stack
void NotifyFavorEvent(void* a_owner, Actor* a_actor, std::uint32_t a_kind, std::uint32_t a_verb, PlayerCharacter* a_player, void* a_arg6, bool a_arg7, bool a_arg8, bool a_arg9, bool a_arg10);

// g_itemEventFilter, g_playerCharacterSingleton: GUESS(low); the names are invented, the image gives only the addresses
extern TESObjectREFR* g_itemEventFilter;
extern PlayerCharacter* g_playerCharacterSingleton;

class TESBoundObject : public TESObject
{
public:
    // IsBoundObject: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
    bool IsBoundObject() const override;
    void* GetBipedObjectForm();  // compared: 0x1d21c0
    void SendActorItemEquippedEvent(TESObjectREFR* a_actor);  // compared: 0x6b70f0
    virtual bool CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3);  // compared: 0x278f90
};
