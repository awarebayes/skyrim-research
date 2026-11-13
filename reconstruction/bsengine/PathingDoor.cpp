// PathingDoor::Slot2, build sse-steam-1-7-104, RVA 0x4e0ed0, 4 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"member-return","generator_version":"2","name_source":{"confidence":"low","kind":"guess","owner":"PathingDoor","rationale":"vtable owner and slot; method spelling invented","slot":2},"template_digest":"1254832e5ca7cdca7f6330a2018dde32919625f6149744dd0138e59a943106d8"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// PathingDoor: EXE_RTTI
// Slot2: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// Method name is a guess built from the vtable owner and slot, not a public symbol.
#include "PathingDoor.h"
// Slot2: GUESS(low); method name inferred from vtable owner and slot
std::uint32_t PathingDoor::Slot2() const
{
    return member;
}
