// BSLightingShaderMaterialSnow functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialsnow
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1528110, 6 bytes: BSLightingShaderMaterialSnow::GetFeature
//   RVA 0x1528090, 46 bytes: BSLightingShaderMaterialSnow::CopyMembers
//   RVA 0x1527fc0, 47 bytes: BSLightingShaderMaterialSnow::Ctor
//   RVA 0x15280d0, 55 bytes: BSLightingShaderMaterialSnow::ComputeCRC32
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLightingShaderMaterialSnow.h"
#include <new>

// SnowDefaults: STANDIN GUESS(low)
using SnowDefaults = BSLightingShaderMaterialSnow::SnowData;
// g_snowDefaults: GUESS(low)
extern SnowDefaults g_snowDefaults;
// BaseCopyHelper: GUESS(low)
void BaseCopyHelper(BSLightingShaderMaterialBase* a_this, BSShaderMaterial* a_src);
// SnowCRCSeed: GUESS(low)
std::uint32_t SnowCRCSeed();
// CRC32Size: GUESS(low)
void CRC32Size(std::uint32_t* a_out, const void* a_data, std::uint32_t a_size);

BSShaderMaterial::Feature BSLightingShaderMaterialSnow::GetFeature() const
{
    return static_cast<Feature>(0xE);
}

void BSLightingShaderMaterialSnow::CopyMembers(BSShaderMaterial* a_src)
{
    BaseCopyHelper(this, a_src);
    unknownA0 = static_cast<BSLightingShaderMaterialSnow*>(a_src)->unknownA0;
}

BSLightingShaderMaterialSnow::BSLightingShaderMaterialSnow() :
    unknownA0(g_snowDefaults)
{}

BSLightingShaderMaterialSnow* BSLightingShaderMaterialSnow::Ctor()
{
    return new (this) BSLightingShaderMaterialSnow;
}

std::uint32_t BSLightingShaderMaterialSnow::ComputeCRC32()
{
    struct SnowBlock {
        SnowData data;
        std::uint32_t seed;
    } block{unknownA0, SnowCRCSeed()};
    std::uint32_t result;
    CRC32Size(&result, &block, 0x14);
    return result;
}
