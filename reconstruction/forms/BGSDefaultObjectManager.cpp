// BGSDefaultObjectManager: constructor, destructor, InitItemImpl and the equip-slot accessors,
// build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CharmedBaryon/CommonLibSSE-NG b93280e (MIT) and the Address
// Library name list. A byte match shows that this source and recipe produce the checked code; it
// does not verify the community method names or that the original source looked like this.
// RVA 0x38fa30, 10 bytes (GetLeftHandEquip); RVA 0x38fa40, 10 bytes (GetRightHandEquip);
// RVA 0x38fa60, 10 bytes (GetVoiceEquip); RVA 0x5d5b70, 29 bytes (GetEquipSlot);
// RVA 0x31bd50, 62 bytes (deleting destructor); RVA 0x31b830, 85 bytes (constructor);
// RVA 0x31bad0, 226 bytes (InitItemImpl).
// Evidence: findings/fourth-batch-selection.md.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/bgsdefaultobjectmanager.cpp:121 (the empty destructor, shape only)
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/bgsdefaultobjectmanager.cpp:112 (the constructor: form type, form ID, reset of the object array; the memset spelling follows ResetFormData at line 15)
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/bgsdefaultobjectmanager.cpp:71 (InitItem: the resolve loop over the default object IDs)
// ~BGSDefaultObjectManager, BGSDefaultObjectManager::BGSDefaultObjectManager: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); names and shape only, offsets and counts are this build's
// Bodies adapted from community sources are listed above; tools/check_origin.py reports none other
// above its threshold at the pinned revisions.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The six functions other than InitItemImpl are compared.
// InitItemImpl is defined here but not compared: a name it binds clashes with an existing symbol-map entry.
#include "BGSDefaultObjectManager.h"

#include <cstring>

// LogProgressMarker, GetDefaultObjectEventSource, SendDefaultObjectEvent, ResolveFormRedirect: GUESS(low); bound by RVA hints
struct DefaultObjectsInitializedEvent {
};
class DefaultObjectEventSource;

void                      LogProgressMarker(const char* a_text);
DefaultObjectEventSource* GetDefaultObjectEventSource();
void                      SendDefaultObjectEvent(DefaultObjectEventSource* a_source, DefaultObjectsInitializedEvent* a_event);
TESForm*                  ResolveFormRedirect(FormID a_formID);

extern DEFAULT_OBJECT_DATA defaultObjectTable[];

static inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// noinline: separate image function that other units call
__declspec(noinline) BGSEquipSlot* BGSDefaultObjectManager::GetLeftHandEquip()
{
    return static_cast<BGSEquipSlot*>(GetDefaultObject(19));
}

// noinline: separate image function that other units call
__declspec(noinline) BGSEquipSlot* BGSDefaultObjectManager::GetRightHandEquip()
{
    return static_cast<BGSEquipSlot*>(GetDefaultObject(20));
}

// noinline: separate image function that other units call
__declspec(noinline) BGSEquipSlot* BGSDefaultObjectManager::GetVoiceEquip()
{
    return static_cast<BGSEquipSlot*>(GetDefaultObject(22));
}

BGSEquipSlot* BGSDefaultObjectManager::GetEquipSlot(std::uint32_t a_which)
{
    if (a_which == 0) {
        return GetLeftHandEquip();
    }
    if (a_which == 1) {
        return GetRightHandEquip();
    }
    if (a_which == 2) {
        return GetVoiceEquip();
    }
    return nullptr;
}

BGSDefaultObjectManager::BGSDefaultObjectManager()
{
    formType = static_cast<FormType>(0x6b);
    SetFormID(0x31, true);
    std::memset(objects, 0, sizeof(objects) + sizeof(objectInit));
}

BGSDefaultObjectManager::~BGSDefaultObjectManager()
{
}

void BGSDefaultObjectManager::InitItemImpl()
{
    if (TestBit(formFlags, 3)) {
        return;
    }
    for (std::uint32_t i = 0; i < kTotal; ++i) {
        if (i == 0x172) {
            LogProgressMarker("It is time");
        }
        if (!objectInit[i]) {
            objects[i] = LookupByID(static_cast<FormID>(reinterpret_cast<std::uintptr_t>(objects[i])));
            if (objects[i] && objects[i]->formType != defaultObjectTable[i].type) {
                if (objects[i]->formType == static_cast<FormType>(0xF)) {
                    objects[i] = ResolveFormRedirect(objects[i]->formID);
                } else {
                    objects[i] = nullptr;
                }
            }
            objectInit[i] = true;
        }
    }
    SetInitialized(true);
    DefaultObjectsInitializedEvent event;
    SendDefaultObjectEvent(GetDefaultObjectEventSource(), &event);
}
