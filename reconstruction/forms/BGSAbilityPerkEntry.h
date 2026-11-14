// BGSAbilityPerkEntry::GetType, build sse-steam-1-7-104, RVA 0x3984c0, 6 bytes.
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
// BGSAbilityPerkEntry: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>

class Actor;
class SpellItem;
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class BGSAbilityPerkEntry
{
public:
    virtual std::uint32_t GetType() const;
    // ApplyPerkEntry, RemovePerkEntry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); no base declaration in this unit, so not override
    virtual void ApplyPerkEntry(Actor* a_actor);
    virtual void RemovePerkEntry(Actor* a_actor);

    std::uint8_t unk08[0x8];  // 08
    SpellItem*   spell;       // 10
    // spell: GUESS(low)
};

// AddSpell, RemoveSpell: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ResetPerkSpells: GUESS(low)
// ResetPerkSpells: the tail callee takes the actor and a float of 0.0
class Actor
{
public:
    void AddSpell(SpellItem* a_spell);
    void RemoveSpell(SpellItem* a_spell);
    void ResetPerkSpells(float a_value);
};
