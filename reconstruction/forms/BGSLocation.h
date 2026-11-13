// BGSLocation type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSLocation, BGSLocation::InitializeData, BGSLocation::~BGSLocation, BGSLocation::parentLoc, BGSLocation::unreportedCrimeFaction, BGSLocation::musicType, BGSLocation::worldLocMarker, BGSLocation::worldLocRadius, BGSLocation::horseLocMarker, BGSLocation::lastChecked, BGSLocation::cleared, BGSLocation::everCleared: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSLocation::clearedFlags: GUESS(low); one 16-bit field for the two flag bytes, which the listing clears with one word store
// gNullHandle: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); the 32-bit null reference handle at RVA 0x219e55c, id 400312; the name there is gNullHandle_*
// BGSLocation::unk70: GUESS(low); opaque bytes for specialRefs to keywordData (offset 0x70 to 0xE8)
// TESFullName, TESFullName::GetFullNameLength, TESFullName::GetFullName: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); size 0x10 and slots only
// TESFullName::unk08: GUESS(low); the 8-byte name member
// BGSKeywordForm, BGSKeywordForm::HasKeyword, BGSKeywordForm::GetDefaultKeyword: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); size 0x18 and slots only
// BGSKeywordForm::unk08: GUESS(low); the keyword array
// BGSKeyword, BGSMusicType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
// TESFaction: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
// BGSLocation::BGSLocation: GUESS(low); the implicit constructor, defined only so the unit emits the vftables and the deleting destructor
// BGSLocation::~BGSLocation: declared and not defined so that the deleting destructor calls the plain one; bound by hint to 0x298250
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSKeyword;
class BGSMusicType;
class TESFaction;

extern std::uint32_t gNullHandle;

class TESFullName : public BaseFormComponent {
public:
    ~TESFullName() override;                                   // 00
    void InitializeDataComponent() override;                   // 01
    void ClearDataComponent() override;                        // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;     // 03
    virtual std::uint32_t GetFullNameLength() const;           // 04
    virtual const char*   GetFullName() const;                 // 05

    std::uint8_t unk08[0x8];  // 08
};
static_assert(sizeof(TESFullName) == 0x10, "layout");

class BGSKeywordForm : public BaseFormComponent {
public:
    ~BGSKeywordForm() override;                                // 00
    void InitializeDataComponent() override;                   // 01
    void ClearDataComponent() override;                        // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;     // 03
    virtual bool        HasKeyword(const BGSKeyword* a_keyword) const;  // 04
    virtual BGSKeyword* GetDefaultKeyword() const;             // 05

    std::uint8_t unk08[0x10];  // 08
};
static_assert(sizeof(BGSKeywordForm) == 0x18, "layout");

class BGSLocation :
    public TESForm,        // 00
    public TESFullName,    // 20
    public BGSKeywordForm  // 30
{
public:
    BGSLocation();
    ~BGSLocation() override;  // 00

    void InitializeData() override;  // 04

    BGSLocation*  parentLoc;               // 48
    TESFaction*   unreportedCrimeFaction;  // 50
    BGSMusicType* musicType;               // 58
    std::uint32_t worldLocMarker;          // 60
    float         worldLocRadius;          // 64
    std::uint32_t horseLocMarker;          // 68
    std::uint32_t pad6C;                   // 6C
    std::uint8_t  unk70[0x78];             // 70
    std::uint32_t lastChecked;             // E8
    // clearedFlags: GUESS(low); the two bytes EC and ED that the listing clears with one word store (cleared and everCleared)
    std::uint16_t clearedFlags;            // EC
    std::uint16_t padEE;                   // EE
};
static_assert(sizeof(BGSLocation) == 0xF0, "layout");
