// BGSEncounterZone form methods, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-bgsencounterzone
// RVA 0x28f5e0, 23 bytes (InitializeData); RVA 0x28fcb0, 48 bytes (Revert); RVA 0x28fe70, 62 bytes
// (~BGSEncounterZone, the deleting destructor); RVA 0x28fc40, 99 bytes (LoadGame); RVA 0x28fbc0,
// 120 bytes (SaveGame); RVA 0x28f9e0, 127 bytes (GetLevel); RVA 0x28f850, 168 bytes (InitItemImpl).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT) and the shape of SaveGame
// read from momusdigital/fnv_decomp@91e1b6e8 src/bgsencounterzone.cpp:302 (names and order of the
// two guarded writes only; no layout taken).
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/bgsencounterzone.cpp:302
// Unnamed callees, bound by hint or position: 0x1e5ae0 GetFile, 0x1e5860 LookupByID, 0x1e6d00 AddCompileIndex,
// 0x1e60b0 SetFormFlag, 0x207b5f8 the level scale float, 0x15a743c the global sized operator delete.
// Bodies adapted from community sources are listed above; tools/check_origin.py reports none other
// above its threshold at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and fnv_decomp 91e1b6e8.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The five functions other than GetLevel and InitItemImpl are compared.
// GetLevel and InitItemImpl are defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "BGSEncounterZone.h"

#include <cstring>
#include <typeinfo>

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value.
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// GetChangeFlags: GUESS(low); the save buffer's change-flag dword sits at 0x1b, unaligned, past the byte TESForm.h models.
static std::uint32_t GetChangeFlags(BGSSaveFormBuffer* a_buf)
{
    return *reinterpret_cast<std::uint32_t*>(&a_buf->unk1B);
}

// Not compared: defined so that this unit emits the vftable and with it the deleting destructor.
BGSEncounterZone::BGSEncounterZone()
{
}

BGSEncounterZone::~BGSEncounterZone()
{
}

void BGSEncounterZone::InitializeData()
{
    std::memset(&data, 0, sizeof(data));
    std::memset(&gameData, 0, sizeof(gameData));
}

void BGSEncounterZone::Revert(BGSLoadFormBuffer* a_buf)
{
    TESForm::Revert(a_buf);
    if (a_buf->oldChangeFlags & ChangeFlags::kGameData) {
        gameData.detachTime = 0;
        gameData.attachTime = 0;
        gameData.resetTime = 0;
        gameData.zoneLevel = 0;
        gameData.pad0D = 0;
    }
}

void BGSEncounterZone::LoadGame(BGSLoadFormBuffer* a_buf)
{
    TESForm::LoadGame(a_buf);
    if (TestBit(a_buf->changeFlags, 1)) {
        std::uint8_t zoneFlags = 0;
        a_buf->LoadDataEndian(&zoneFlags, 1, 1);
    }
    if (a_buf->changeFlags & ChangeFlags::kGameData) {
        a_buf->LoadDataEndian(&gameData, 16, 1);
    }
}

void BGSEncounterZone::SaveGame(BGSSaveFormBuffer* a_buf)
{
    TESForm::SaveGame(a_buf);
    if (TestBit(GetChangeFlags(a_buf), 1)) {
        std::uint8_t zoneFlags = data.flags & 1;
        a_buf->SaveDataEndian(&zoneFlags, 1, 1, 0);
    }
    if (GetChangeFlags(a_buf) & ChangeFlags::kGameData) {
        a_buf->SaveDataEndian(&gameData, 16, 1, 0);
    }
}

std::uint16_t BGSEncounterZone::GetLevel()
{
    std::uint16_t level = PlayerCharacter::singleton->GetLevel();
    if (level < data.minLevel) {
        if (!TestBit(static_cast<std::int32_t>(static_cast<std::int8_t>(data.flags)), 1)) {
            level = data.minLevel;
        }
    } else {
        level = static_cast<std::uint16_t>(static_cast<float>(level - data.minLevel) * kLevelScale + static_cast<float>(data.minLevel));
    }
    if (data.maxLevel) {
        return data.maxLevel < level ? data.maxLevel : level;
    }
    return level;
}

void BGSEncounterZone::InitItemImpl()
{
    if (!TestBit(formFlags, 3)) {
        std::uint32_t id = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(data.zoneOwner));
        if (id != 0) {
            AddCompileIndex(id, GetFile(-1));
            data.zoneOwner = LookupByID(id);
        }
        id = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(data.location));
        if (id != 0) {
            AddCompileIndex(id, GetFile(-1));
            data.location = dynamic_cast<BGSLocation*>(LookupByID(id));
        }
        SetFormFlag(true);
    }
}
