// BGSQueuedObjectInitialLoad::Slot5, build sse-steam-1-7-104, RVA 0x51c720, 6 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"low","kind":"guess","owner":"BGSQueuedObjectInitialLoad","rationale":"vtable owner and slot; method spelling invented","slot":5},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// BGSQueuedObjectInitialLoad: EXE_RTTI
// Slot5: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// Method name is a guess built from the vtable owner and slot, not a public symbol.
#pragma once
#include <cstdint>
// Slot5: GUESS(low); method name inferred from vtable owner and slot
class BGSQueuedObjectInitialLoad
{
public:
    virtual std::uint32_t Slot5() const;
};
