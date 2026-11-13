// TESRegionDataMap::GetType, build sse-steam-1-7-104, RVA 0x251e60, 6 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"medium","kind":"public","repository":"meh321/AddressLibraryDatabase","revision":"0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91","source":"meh321"},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// TESRegionDataMap: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESRegionDataObj: GUESS(low); the object returned by slot 4 of TESRegionDataMap; only slot 6 is called
class TESRegionDataObj
{
public:
    virtual void Slot0() {}
    virtual void Slot1() {}
    virtual void Slot2() {}
    virtual void Slot3() {}
    virtual void Slot4() {}
    virtual void Slot5() {}
    virtual void Slot6(void* a_param, std::int32_t a_count) {}  // 30
};

// TESRegionDataMap: slot 4 is a placeholder returning the object that Unk_05 forwards to
// IsLoaded: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x2520b0
// Unk_05: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x251f10; the community return type is void, while the listing returns the forwarded object in RAX
// TESRegionDataObj::Slot6 and the slot placeholders: GUESS(low); slot numbers come from the listing offsets
class TESRegionDataMap
{
public:
    virtual std::uint32_t GetType() const;
    virtual void Slot1() {}
    virtual void Slot2() {}
    virtual void Slot3() {}
    virtual TESRegionDataObj* Slot4() { return nullptr; }  // 20
    virtual void Slot5() {}
    virtual bool IsLoaded() const;  // compared: 0x2520b0
    virtual TESRegionDataObj* Unk_05(void* a_param);  // compared: 0x251f10
};
