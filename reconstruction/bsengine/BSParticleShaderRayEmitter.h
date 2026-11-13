// BSParticleShaderRayEmitter::Slot6, build sse-steam-1-7-104, RVA 0x15362a0, 8 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"member-return","generator_version":"2","name_source":{"confidence":"low","kind":"guess","owner":"BSParticleShaderRayEmitter","rationale":"vtable owner and slot; method spelling invented","slot":6},"template_digest":"1254832e5ca7cdca7f6330a2018dde32919625f6149744dd0138e59a943106d8"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// BSParticleShaderRayEmitter: EXE_RTTI
// Slot6: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// Method name is a guess built from the vtable owner and slot, not a public symbol.
#pragma once
#include <cstdint>
// Slot6: GUESS(low); method name inferred from vtable owner and slot
class BSParticleShaderRayEmitter
{
public:
    virtual void* Slot6() const;
    std::uint8_t padding[0xed8];
    void* member;
};
