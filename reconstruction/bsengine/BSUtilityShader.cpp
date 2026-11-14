// BSUtilityShader functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsutilityshader
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x15673e0, 3 bytes: BSUtilityShader::RestoreMaterial
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSUtilityShader.h"

// RestoreMaterial: the target has no work to do.
void BSUtilityShader::RestoreMaterial(const BSShaderMaterial* a_material)
{
}
