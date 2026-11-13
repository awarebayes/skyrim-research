// BSWaterShaderMaterial::GetType, build sse-steam-1-7-104, RVA 0x155af30, 6 bytes.
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
// Task p92-s-bswatershadermaterial: RVA 0x155ae20 (GetDefault) and 0x155aef0 (deleting destructor) are compared alongside GetType.
// Evidence: findings/fifth-batch-selection.md
// BSWaterShaderMaterial: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#include "BSWaterShaderMaterial.h"

// BSWaterShaderMaterial::BSWaterShaderMaterial: GUESS(low); defined so the vftable and the deleting destructor are emitted
BSWaterShaderMaterial::BSWaterShaderMaterial()
{
}

// BSWaterShaderMaterial::GetDefault: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
BSWaterShaderMaterial* BSWaterShaderMaterial::GetDefault()
{
    return g_BSWaterShaderMaterialDefault;
}

// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
std::uint32_t BSWaterShaderMaterial::GetType() const
{
    return 0x3;
}
