// BSShader functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsshader
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-4), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1578910, 3 bytes: BSShader::SetupMaterial
//   RVA 0x1578920, 3 bytes: BSShader::RestoreMaterial
//   RVA 0x1578ac0, 3 bytes: BSShader::GetTechniqueName
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSShader.h"

// Body done: RVA 0x1578910, 3 bytes, BSShader::SetupMaterial.
void BSShader::SetupMaterial(const BSShaderMaterial* a_material)
{
}

// Body done: RVA 0x1578920, 3 bytes, BSShader::RestoreMaterial.
void BSShader::RestoreMaterial(const BSShaderMaterial* a_material)
{
}

// Body done: RVA 0x1578ac0, 3 bytes, BSShader::GetTechniqueName.
void BSShader::GetTechniqueName(std::uint32_t a_techniqueID, char* a_buffer, std::uint32_t a_bufferSize)
{
}
