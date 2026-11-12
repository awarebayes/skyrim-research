// TESRace accessors and destructor, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x3ebda0, 10 bytes (GetPlayable).
// RVA 0x3e6250, 22 bytes (GetBodyPartData).
// RVA 0x3ebd80, 22 bytes (GetFormEditorID).
// RVA 0x3e64a0, 24 bytes (GetMovementType).
// RVA 0x3eb840, 52 bytes (scalar deleting destructor of TESRace).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above other than GetFormEditorID are compared.
// GetFormEditorID is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "TESRace.h"

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
TESRace::TESRace()
{
}

bool TESRace::GetPlayable() const
{
    return TestBit(data.flags, 0);
}

BGSBodyPartData* TESRace::GetBodyPartData()
{
    return bodyPartData ? bodyPartData : defaultBodyPartData;
}

const char* TESRace::GetFormEditorID() const
{
    return formEditorID.c_str();
}

BGSMovementType* TESRace::GetMovementType(std::int32_t a_index)
{
    BGSMovementType* type = baseMoveTypes[a_index];
    if (type) {
        return type;
    }
    return BGSDefaultObjectManager::GetDefaultMovementType(a_index);
}
