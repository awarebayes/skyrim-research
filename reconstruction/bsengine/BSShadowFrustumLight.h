// BSShadowFrustumLight::Slot4, build sse-steam-1-7-104, RVA 0x1587f70, 3 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"low","kind":"guess","owner":"BSShadowFrustumLight","rationale":"vtable owner and slot; method spelling invented","slot":4},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// BSShadowFrustumLight: EXE_RTTI
// Slot4: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// Method name is a guess built from the vtable owner and slot, not a public symbol.
// Licence: the name GetIsFrustumLight comes from powerof3/CommonLibSSE (GPL-3.0), so this file is GPL-3.0.
#pragma once
#include <cstdint>
// Slot4: GUESS(low); method name inferred from vtable owner and slot
// BSShadowFrustumLight::GetIsFrustumLight: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); GPL-3.0 applies to the name in this file; compared at RVA 0x1587f80
class BSShadowFrustumLight
{
public:
    virtual std::uint8_t Slot4() const;
    virtual bool GetIsFrustumLight();  // compared: 0x1587f80
};
