// TESObjectBOOK declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-tesobjectbook
// Source exposure: mixed (names and declarations from community headers; base classes, offsets and
// the compared functions from the pinned image).
// Base form: shared header ../forms/TESForm.h for TESForm and its buffer types (BGSLoadFormBuffer,
// BGSSaveFormBuffer, BGSLoadGameBuffer, BGSSaveGameBuffer). The other shared buffer headers
// (BGSLoadGameBuffer.h, BGSSaveFormBuffer.h) redefine TESForm and the buffers, so they cannot be
// included with TESForm.h; header-gap BGSLoadGameBuffer and BGSSaveFormBuffer.
// TESObjectBOOK: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// InitializeData, LoadGame, SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares OBJ_BOOK data, a 0x10-byte struct, and this file declares its first eight bytes
// teaches: GUESS(low); the community header puts this union at +8 of OBJ_BOOK data, declared here as eight bytes
// inventoryModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESObjectSTAT: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); forward declaration only
// TESObject, TESBoundObject: STANDIN EXE_RTTI; empty stand-ins over TESForm, the NG bases are not declared
// unk20, unk88: GUESS(low); the NG bases TESFullName, TESModelTextureSwap, TESIcon and TESValueForm sit in this range and are kept as bytes
// LoadBaseSubobject, SaveBaseSubobject: GUESS(low); the image calls them on this+0x88 with the buffer; the names are invented
// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only IsCrimeToActivate and GetDisplayFullName are declared
// IsCrimeToActivate, GetDisplayFullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// g_activateVerbPlain, g_activateVerbTake, g_activateVerbSteal, FormatString: GUESS(low); the globals hold string pointers the image selects between, the format helper takes a format and two strings
// BSString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class BSString;
class TESObjectREFR;
class TESObjectSTAT;

// TESObject: STANDIN EXE_RTTI
class TESObject : public TESForm
{
public:
};

// TESBoundObject: STANDIN EXE_RTTI
class TESBoundObject : public TESObject
{
public:
};

// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the two members the activate text uses are declared
class TESObjectREFR
{
public:
    bool        IsCrimeToActivate();  // 0x2f4a50
    const char* GetDisplayFullName(); // 0x2f08d0
};

// LoadBaseSubobject, SaveBaseSubobject: GUESS(low); the image calls them with the address of this+0x88 and the buffer
void LoadBaseSubobject(void* a_sub, BGSLoadFormBuffer* a_buf);
void SaveBaseSubobject(void* a_sub, BGSSaveFormBuffer* a_buf);

// g_activateVerbPlain, g_activateVerbTake, g_activateVerbSteal: GUESS(low); the globals hold string pointers the image selects between
extern const char* g_activateVerbPlain;
extern const char* g_activateVerbTake;
extern const char* g_activateVerbSteal;

// FormatString: GUESS(low); the image calls it with the destination, a format and two strings
void FormatString(BSString& a_dst, const char* a_fmt, const char* a_first, const char* a_second);

class TESObjectBOOK : public TESBoundObject
{
public:
    TESObjectBOOK();
    virtual void InitializeData();  // compared: 0x27f830
    virtual void LoadGame(BGSLoadFormBuffer* a_buf);  // compared: 0x280540
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared: 0x2804e0
    virtual bool GetActivateText(TESObjectREFR* a_activator, BSString& a_dst);  // compared: 0x280210

    // unk20: GUESS(low); bytes up to the sub-object at 0x88
    std::uint8_t unk20[0x68];  // 20
    // unk88: GUESS(low); the sub-object that LoadGame and SaveGame pass to their helpers
    std::uint8_t unk88[0x88];  // 88
    // data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; flags and type are its first bytes, read by GetActivateText and the save and load pair
    std::uint64_t data;  // 110
    // teaches: GUESS(low); the community header puts this union at +8 of OBJ_BOOK data
    std::uint64_t teaches;  // 118
    // inventoryModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    TESObjectSTAT* inventoryModel;  // 120
};
