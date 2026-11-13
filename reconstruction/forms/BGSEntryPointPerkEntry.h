// BGSEntryPointPerkEntry::GetType, build sse-steam-1-7-104, RVA 0x3984d0, 6 bytes.
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
// BGSEntryPointPerkEntry: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstddef>
#include <cstdint>
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class Actor;
class BGSEntryPointPerkEntry;

// EntryPoint: GUESS(low); one-byte enum, the listing zero-extends the stored byte
enum class EntryPoint : std::uint8_t {};

// RemoveEntryPointFromActor: GUESS(low); the tail-call target at RVA 0x69f970, bound by hint; takes the actor first
void RemoveEntryPointFromActor(Actor* a_actor, BGSEntryPointPerkEntry* a_entry);

// BGSEntryPointPerkEntry::GetFunction, BGSEntryPointPerkEntry::GetFunctionData, BGSEntryPointPerkEntry::RemovePerkEntry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x398480, 0x3984a0, 0x396750
// function: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the byte at offset 0x11 from the listing
// functionData: GUESS(low); the pointer at offset 0x18 from the listing, the padding fills the gap
class BGSEntryPointPerkEntry
{
public:
    virtual std::uint32_t GetType() const;
    virtual EntryPoint GetFunction();  // compared: 0x398480
    virtual void* GetFunctionData() const;  // compared: 0x3984a0
    virtual void RemovePerkEntry(Actor* a_actor);  // compared: 0x396750

    std::uint8_t unk08[0x9];  // 08
    std::uint8_t function;    // 11
    std::uint8_t unk12[0x6];  // 12
    void*        functionData;  // 18
};
static_assert(offsetof(BGSEntryPointPerkEntry, function) == 0x11, "BGSEntryPointPerkEntry::function offset");
static_assert(offsetof(BGSEntryPointPerkEntry, functionData) == 0x18, "BGSEntryPointPerkEntry::functionData offset");
