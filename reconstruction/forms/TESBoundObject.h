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
    bool Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t a_targetCount) override;
    // IsBoundObject: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
    bool IsBoundObject() const override;
    void LoadObjectBound(TESFile*) override;
    void* GetBipedObjectForm();  // compared: 0x1d21c0
    void SendActorItemEquippedEvent(TESObjectREFR* a_actor);  // compared: 0x6b70f0
    virtual bool CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3);  // compared: 0x278f90
};

// TESFile: STANDIN GUESS(low); only the relevant flag and calls
class TESFile { public: std::uint32_t GetCurrentSubRecordType(); bool ReadData(void*, std::uint32_t); std::uint8_t pad[0x2e9]; std::uint8_t swap; };


// ActorActivateView: STANDIN GUESS(low); polymorphic view exposing only the observed call slot
class ActorActivateView
{
public:
    // UnknownSlot0: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot0();
    // UnknownSlot1: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot1();
    // UnknownSlot2: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot2();
    // UnknownSlot3: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot3();
    // UnknownSlot4: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot4();
    // UnknownSlot5: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot5();
    // UnknownSlot6: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot6();
    // UnknownSlot7: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot7();
    // UnknownSlot8: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot8();
    // UnknownSlot9: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot9();
    // UnknownSlot10: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot10();
    // UnknownSlot11: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot11();
    // UnknownSlot12: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot12();
    // UnknownSlot13: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot13();
    // UnknownSlot14: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot14();
    // UnknownSlot15: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot15();
    // UnknownSlot16: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot16();
    // UnknownSlot17: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot17();
    // UnknownSlot18: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot18();
    // UnknownSlot19: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot19();
    // UnknownSlot20: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot20();
    // UnknownSlot21: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot21();
    // UnknownSlot22: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot22();
    // UnknownSlot23: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot23();
    // UnknownSlot24: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot24();
    // UnknownSlot25: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot25();
    // UnknownSlot26: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot26();
    // UnknownSlot27: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot27();
    // UnknownSlot28: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot28();
    // UnknownSlot29: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot29();
    // UnknownSlot30: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot30();
    // UnknownSlot31: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot31();
    // UnknownSlot32: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot32();
    // UnknownSlot33: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot33();
    // UnknownSlot34: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot34();
    // UnknownSlot35: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot35();
    // UnknownSlot36: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot36();
    // UnknownSlot37: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot37();
    // UnknownSlot38: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot38();
    // UnknownSlot39: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot39();
    // UnknownSlot40: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot40();
    // UnknownSlot41: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot41();
    // UnknownSlot42: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot42();
    // UnknownSlot43: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot43();
    // UnknownSlot44: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot44();
    // UnknownSlot45: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot45();
    // UnknownSlot46: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot46();
    // UnknownSlot47: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot47();
    // UnknownSlot48: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot48();
    // UnknownSlot49: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot49();
    // UnknownSlot50: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot50();
    // UnknownSlot51: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot51();
    // UnknownSlot52: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot52();
    // UnknownSlot53: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot53();
    // UnknownSlot54: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot54();
    // UnknownSlot55: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot55();
    // UnknownSlot56: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot56();
    // UnknownSlot57: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot57();
    // UnknownSlot58: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot58();
    // UnknownSlot59: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot59();
    // UnknownSlot60: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot60();
    // UnknownSlot61: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot61();
    // UnknownSlot62: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot62();
    // UnknownSlot63: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot63();
    // UnknownSlot64: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot64();
    // UnknownSlot65: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot65();
    // UnknownSlot66: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot66();
    // UnknownSlot67: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot67();
    // UnknownSlot68: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot68();
    // UnknownSlot69: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot69();
    // UnknownSlot70: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot70();
    // UnknownSlot71: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot71();
    // UnknownSlot72: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot72();
    // UnknownSlot73: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot73();
    // UnknownSlot74: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot74();
    // UnknownSlot75: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot75();
    // UnknownSlot76: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot76();
    // UnknownSlot77: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot77();
    // UnknownSlot78: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot78();
    // UnknownSlot79: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot79();
    // UnknownSlot80: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot80();
    // UnknownSlot81: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot81();
    // UnknownSlot82: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot82();
    // UnknownSlot83: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot83();
    // UnknownSlot84: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot84();
    // UnknownSlot85: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot85();
    // UnknownSlot86: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot86();
    // UnknownSlot87: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot87();
    // UnknownSlot88: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot88();
    // UnknownSlot89: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot89();
    // UnknownSlot90: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot90();
    // UnknownSlot91: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot91();
    // UnknownSlot92: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot92();
    // UnknownSlot93: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot93();
    // UnknownSlot94: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot94();
    // UnknownSlot95: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot95();
    // UnknownSlot96: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot96();
    // UnknownSlot97: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot97();
    // UnknownSlot98: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot98();
    // UnknownSlot99: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot99();
    // UnknownSlot100: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot100();
    // UnknownSlot101: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot101();
    // UnknownSlot102: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot102();
    // UnknownSlot103: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot103();
    // UnknownSlot104: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot104();
    // UnknownSlot105: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot105();
    // UnknownSlot106: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot106();
    // UnknownSlot107: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot107();
    // UnknownSlot108: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot108();
    // UnknownSlot109: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot109();
    // UnknownSlot110: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot110();
    // UnknownSlot111: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot111();
    // UnknownSlot112: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot112();
    // UnknownSlot113: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot113();
    // UnknownSlot114: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot114();
    // UnknownSlot115: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot115();
    // UnknownSlot116: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot116();
    // UnknownSlot117: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot117();
    // UnknownSlot118: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot118();
    // UnknownSlot119: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot119();
    // UnknownSlot120: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot120();
    // UnknownSlot121: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot121();
    // UnknownSlot122: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot122();
    // UnknownSlot123: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot123();
    // UnknownSlot124: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot124();
    // UnknownSlot125: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot125();
    // UnknownSlot126: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot126();
    // UnknownSlot127: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot127();
    // UnknownSlot128: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot128();
    // UnknownSlot129: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot129();
    // UnknownSlot130: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot130();
    // UnknownSlot131: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot131();
    // UnknownSlot132: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot132();
    // UnknownSlot133: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot133();
    // UnknownSlot134: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot134();
    // UnknownSlot135: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot135();
    // UnknownSlot136: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot136();
    // UnknownSlot137: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot137();
    // UnknownSlot138: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot138();
    // UnknownSlot139: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot139();
    // UnknownSlot140: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot140();
    // UnknownSlot141: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot141();
    // UnknownSlot142: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot142();
    // UnknownSlot143: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot143();
    // UnknownSlot144: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot144();
    // UnknownSlot145: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot145();
    // UnknownSlot146: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot146();
    // UnknownSlot147: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot147();
    // UnknownSlot148: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot148();
    // UnknownSlot149: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot149();
    // UnknownSlot150: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot150();
    // UnknownSlot151: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot151();
    // UnknownSlot152: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot152();
    // UnknownSlot153: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot153();
    // UnknownSlot154: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot154();
    // UnknownSlot155: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot155();
    // UnknownSlot156: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot156();
    // UnknownSlot157: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot157();
    // UnknownSlot158: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot158();
    // UnknownSlot159: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot159();
    // UnknownSlot160: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot160();
    // UnknownSlot161: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot161();
    // UnknownSlot162: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot162();
    // UnknownSlot163: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot163();
    // UnknownSlot164: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot164();
    // UnknownSlot165: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot165();
    // UnknownSlot166: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot166();
    // UnknownSlot167: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot167();
    // UnknownSlot168: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot168();
    // UnknownSlot169: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot169();
    // UnknownSlot170: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot170();
    // UnknownSlot171: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot171();
    // UnknownSlot172: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot172();
    // UnknownSlot173: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot173();
    // UnknownSlot174: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot174();
    // UnknownSlot175: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot175();
    // UnknownSlot176: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot176();
    // UnknownSlot177: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot177();
    // UnknownSlot178: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot178();
    // UnknownSlot179: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot179();
    // UnknownSlot180: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot180();
    // UnknownSlot181: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot181();
    // UnknownSlot182: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot182();
    // UnknownSlot183: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot183();
    // UnknownSlot184: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot184();
    // UnknownSlot185: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot185();
    // UnknownSlot186: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot186();
    // UnknownSlot187: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot187();
    // UnknownSlot188: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot188();
    // UnknownSlot189: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot189();
    // UnknownSlot190: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot190();
    // UnknownSlot191: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot191();
    // UnknownSlot192: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot192();
    // UnknownSlot193: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot193();
    // UnknownSlot194: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot194();
    // UnknownSlot195: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot195();
    // UnknownSlot196: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot196();
    // UnknownSlot197: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot197();
    // UnknownSlot198: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot198();
    // UnknownSlot199: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot199();
    // UnknownSlot200: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot200();
    // UnknownSlot201: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot201();
    // UnknownSlot202: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot202();
    // UnknownSlot203: GUESS(low); unobserved preceding virtual slot
    virtual void UnknownSlot203();
    // ActivateTarget: GUESS(low); target call through virtual slot 204
    virtual void ActivateTarget(TESObjectREFR*, std::int32_t, std::uint8_t, bool);
};
// RuntimeTypeDescriptor, g_actorType, g_referenceType, CastReferenceToActor: GUESS(low); external RTTI addresses and observed runtime cast
struct RuntimeTypeDescriptor;
extern RuntimeTypeDescriptor g_actorType;
extern RuntimeTypeDescriptor g_referenceType;
ActorActivateView* CastReferenceToActor(TESObjectREFR*, std::int32_t, RuntimeTypeDescriptor*, RuntimeTypeDescriptor*, std::int32_t);
