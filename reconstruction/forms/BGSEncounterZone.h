// BGSEncounterZone type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT):
// include/RE/B/BGSEncounterZone.h. TESForm comes from the shared header TESForm.h.
// BGSEncounterZone, ::InitializeData, ::SaveGame, ::LoadGame, ::Revert, ::InitItemImpl, ::data, ::gameData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSEncounterZone::~BGSEncounterZone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
// BGSEncounterZone::GetLevel: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); non-virtual, returns the level the zone yields
// ENCOUNTER_ZONE_DATA, ::zoneOwner, ::location, ::ownerRank, ::minLevel, ::flags, ::maxLevel, ::pad14: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); plain integers for the stl::enumeration flags, the owner is a TESForm* here
// ENCOUNTER_ZONE_GAME_DATA, ::detachTime, ::attachTime, ::resetTime, ::zoneLevel, ::pad0D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSEncounterZone::ChangeFlags, ::kZoneFlags, ::kGameData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSEncounterZone::AddCompileIndex, ::GetFile, ::LookupByID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares them on TESForm (RVAs 0x1e6d00, 0x1e5ae0, 0x1e5860), declared here because TESForm.h has none (header-gap TESForm)
// BGSEncounterZone::SetFormFlag: GUESS(low); a non-virtual TESForm helper at 0x1e60b0 taking this and a bool, called at the end of InitItemImpl (header-gap TESForm)
// BGSEncounterZone::GetChangeFlags: GUESS(low); reads the dword at offset 0x1b of the save buffer, which TESForm.h models as a byte (header-gap BGSSaveFormBuffer)
// BGSEncounterZone::kLevelScale: GUESS(low); a float in .data at RVA 0x207b5f8 scaling the level above the zone minimum
// BGSLocation: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the type is needed for the dynamic cast
// PlayerCharacter, PlayerCharacter::GetLevel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG derives from Actor, the stand-in declares GetLevel (Actor::GetLevel at 0x6797a0) and the Singleton global (0x3230778) directly
// PlayerCharacter::singleton: GUESS(low); NG reaches the global through an Offset id, the member is a name for the pointer at RVA 0x3230778
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSLocation : public TESForm {
};

class PlayerCharacter {
public:
    std::uint16_t GetLevel() const;

    static PlayerCharacter* singleton;
};

struct ENCOUNTER_ZONE_DATA {
    TESForm*      zoneOwner;  // 00
    BGSLocation*  location;   // 08
    std::int8_t   ownerRank;  // 10
    std::uint8_t  minLevel;   // 11
    std::uint8_t  flags;      // 12
    std::uint8_t  maxLevel;   // 13
    std::uint32_t pad14;      // 14
};
static_assert(sizeof(ENCOUNTER_ZONE_DATA) == 0x18, "layout");

struct ENCOUNTER_ZONE_GAME_DATA {
    std::uint32_t detachTime;  // 00
    std::uint32_t attachTime;  // 04
    std::uint32_t resetTime;   // 08
    std::uint16_t zoneLevel;   // 0C
    std::uint16_t pad0D;       // 0E
};
static_assert(sizeof(ENCOUNTER_ZONE_GAME_DATA) == 0x10, "layout");

class BGSEncounterZone : public TESForm {
public:
    struct ChangeFlags {
        enum ChangeFlag : std::uint32_t {
            kZoneFlags = 1 << 1,
            kGameData  = static_cast<std::uint32_t>(1) << 31
        };
    };

    BGSEncounterZone();
    ~BGSEncounterZone() override;  // 00

    // override (TESForm)
    void InitializeData() override;                    // 04
    void SaveGame(BGSSaveFormBuffer* a_buf) override;  // 0E
    void LoadGame(BGSLoadFormBuffer* a_buf) override;  // 0F
    void Revert(BGSLoadFormBuffer* a_buf) override;    // 12
    void InitItemImpl() override;                      // 13

    std::uint16_t GetLevel();

    static void     AddCompileIndex(std::uint32_t& a_id, TESFile* a_file);
    TESFile*        GetFile(std::int32_t a_idx = -1) const;
    static TESForm* LookupByID(std::uint32_t a_formID);
    void            SetFormFlag(bool a_set);

    static float kLevelScale;

    // members
    ENCOUNTER_ZONE_DATA      data;      // 20
    ENCOUNTER_ZONE_GAME_DATA gameData;  // 38
};
static_assert(sizeof(BGSEncounterZone) == 0x48, "layout");
