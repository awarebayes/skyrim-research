// TESRegionDataSound::GetType, build sse-steam-1-7-104, RVA 0x253310, 6 bytes.
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
// TESRegionDataSound: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstddef>
#include <cstdint>
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESRegionDataSoundObj: GUESS(low); the object returned by slot 4 of TESRegionDataSound; only slot 6 is called
class TESRegionDataSoundObj
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

// IsLoaded: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x2535b0
// Unk_05: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x253410; the community return type is void, while the listing returns the forwarded object in RAX
// Slot1, Slot2, Slot3, Slot4, Slot5: GUESS(low); placeholders so the call offsets 0x20 and 0x30 match the listing
// member10: GUESS(low); the pointer at offset 0x10 from the listing, the padding fills the gap
class TESRegionDataSound
{
public:
    virtual std::uint32_t GetType() const;
    virtual void Slot1() {}
    virtual void Slot2() {}
    virtual void Slot3() {}
    virtual TESRegionDataSoundObj* Slot4() { return nullptr; }  // 20
    virtual void Slot5() {}
    virtual bool IsLoaded() const;  // compared: 0x2535b0
    virtual TESRegionDataSoundObj* Unk_05(void* a_param);  // compared: 0x253410

    std::uint8_t unk08[0x8];  // 08
    void*        member10;    // 10
};
static_assert(offsetof(TESRegionDataSound, member10) == 0x10, "TESRegionDataSound::member10 offset");
