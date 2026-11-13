// BGSPerkEntry::GetID, build sse-steam-1-7-104, RVA 0x395b20, 6 bytes.
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
// BGSPerkEntry: EXE_RTTI
// GetID: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// GetID: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class BGSPerk;

// BGSPerkEntry::SetParent, BGSPerkEntry::CheckConditionFilters, BGSPerkEntry::ClearData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x395b10, 0x398460, 0x398470
class BGSPerkEntry
{
public:
    virtual std::uint32_t GetID() const;
    virtual void SetParent(BGSPerk* a_parent);  // compared: 0x395b10
    virtual bool CheckConditionFilters(std::uint32_t a_numArgs, void* a_args);  // compared: 0x398460
    virtual void ClearData();  // compared: 0x398470
};
