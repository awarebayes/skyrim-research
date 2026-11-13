// TESRegionGrassObject::Slot1, build sse-steam-1-7-104, RVA 0x254570, 6 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"low","kind":"guess","owner":"TESRegionGrassObject","rationale":"vtable owner and slot; method spelling invented","slot":1},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// TESRegionGrassObject: EXE_RTTI
// Slot1: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// Method name is a guess built from the vtable owner and slot, not a public symbol.
#include "TESRegionGrassObject.h"
// Slot1: GUESS(low); method name inferred from vtable owner and slot
std::uint32_t TESRegionGrassObject::Slot1() const
{
    return 0x1;
}
