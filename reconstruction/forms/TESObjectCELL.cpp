// TESObjectCELL member functions, build sse-steam-1-7-104.
//
// Labels: v2
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local listings of the pinned image
// with types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Compared functions (RVA, size):
//   EnterReferenceListLock RVA 0x2cbed0, 14 bytes
//   GetbhkWorld            RVA 0x2be9b0, 26 bytes
//   GetCoordinates         RVA 0x2bc660, 34 bytes
//   ExitReferenceListLock  RVA 0x2cbef0, 78 bytes
//   GetEncounterZone       RVA 0x2be700, 79 bytes
//   GetOwner               RVA 0x2be530, 148 bytes
//   GetLocation            RVA 0x2bb180, 320 bytes; passes attempts, but no match record yet: the
//     repository symbol map holds its name unsized, and sizing that entry would invalidate others
// SetFormEditorID, ClearData and Revert are not part of this unit yet (thread-local guard).
// A byte match shows this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectCELL.h"

void TESObjectCELL::EnterReferenceListLock()
{
    spinLock.Lock();
}

bhkWorld* TESObjectCELL::GetbhkWorld() const
{
    if (cellFlags & 1) {
        return extraList.GetbhkWorld();
    }
    return *gExteriorbhkWorld;
}

void TESObjectCELL::GetCoordinates(std::int32_t& a_x, std::int32_t& a_y)
{
    EXTERIOR_DATA* exterior = (cellFlags & 1) ? nullptr : cellData.exterior;
    if (exterior) {
        a_x = exterior->cellX;
        a_y = exterior->cellY;
        return;
    }
    a_x = 0;
    a_y = 0;
}

void TESObjectCELL::ExitReferenceListLock()
{
    spinLock.Unlock();
}

BGSEncounterZone* TESObjectCELL::GetEncounterZone() const
{
    if (loadedData) {
        return loadedData->encounterZone;
    }
    BGSEncounterZone* zone = extraList.GetEncounterZone();
    if (!zone && !(cellFlags & 1) && worldSpace) {
        zone = worldSpace->encounterZone;
    }
    return zone;
}

TESForm* TESObjectCELL::GetOwner()
{
    TESForm* owner = extraList.GetOwner();
    if (!owner) {
        BGSEncounterZone* zone = GetEncounterZone();
        if (zone && zone != gDefaultEncounterZone) {
            owner = zone->zoneOwner;
        }
    }
    return owner;
}

BGSLocation* TESObjectCELL::GetLocation() const
{
    BGSEncounterZone* zone = GetEncounterZone();
    zone = ResolveFormRef(this, zone);
    if (zone && zone != gDefaultEncounterZone) {
        BGSLocation* location = ResolveFormRef(zone, zone->location);
        if (location) {
            return location;
        }
    }
    BGSLocation* location = extraList.GetExtraLocation();
    if (!location && !(cellFlags & 1) && worldSpace) {
        return worldSpace->GetLocation();
    }
    return location;
}
