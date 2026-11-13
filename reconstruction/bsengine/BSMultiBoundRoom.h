// BSMultiBoundRoom::RegisterStreamables, build sse-steam-1-7-104, RVA 0xfcdb40, 3 bytes.
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
// Task p92-s-bsmultiboundroom: CreateClone (0xfcdb10), LoadBinary (0xfcdb20) and LinkObject (0xfcdb30) are added beside RegisterStreamables.
// BSMultiBoundRoom: EXE_RTTI
// RegisterStreamables: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// RegisterStreamables: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class BSMultiBoundRoom
{
public:
    virtual std::uint8_t RegisterStreamables() const;
    // CreateClone, LoadBinary, LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declared on NiObject there and inherited, not declared on this class
    virtual void* CreateClone(void* a_cloning);
    virtual void LoadBinary(void* a_stream);
    virtual void LinkObject(void* a_stream);
};
