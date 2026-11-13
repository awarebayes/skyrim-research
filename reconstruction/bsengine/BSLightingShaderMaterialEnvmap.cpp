// BSLightingShaderMaterialEnvmap functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bslightingshadermaterialenvmap
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1525020, 82 bytes: BSLightingShaderMaterialEnvmap::SaveBinary
//   RVA 0x1525080, 82 bytes: BSLightingShaderMaterialEnvmap::LoadBinary
//   RVA 0x1524ce0, 161 bytes: BSLightingShaderMaterialEnvmap::ComputeCRC32
// Set aside in near-miss/ after two to five counted attempts each: 0x1524a60 Ctor, 0x1524f10
// ReceiveValuesFromRootMaterial, 0x1524f80 GetTextures.
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSLightingShaderMaterialEnvmap.h"

// RVA 0x1525020, 82 bytes: the base writes its own fields, then this writes the float.
void BSLightingShaderMaterialEnvmap::SaveBinary(NiStream& a_stream)
{
    BSLightingShaderMaterialBase::SaveBinary(a_stream);
    std::uint32_t componentSize = 4;
    a_stream.oStr->binary_write(&unkB0, 4, &componentSize);
}

// RVA 0x1525080, 82 bytes: the mirror of SaveBinary on the input stream.
void BSLightingShaderMaterialEnvmap::LoadBinary(NiStream& a_stream)
{
    BSLightingShaderMaterialBase::LoadBinary(a_stream);
    std::uint32_t componentSize = 4;
    a_stream.iStr->binary_read(&unkB0, 4, &componentSize);
}
// EnvmapCrcRecord: GUESS(low); the 0x10-byte record hashed by ComputeCRC32, laid out as the image writes it
struct EnvmapCrcRecord
{
    std::uint32_t ids[2];    // 00
    float         unkB0;     // 08
    std::uint32_t flagHash;  // 0C
};
static_assert(sizeof(EnvmapCrcRecord) == 0x10, "EnvmapCrcRecord size");

// RVA 0x1524ce0, 161 bytes: hashes the two texture ids, the float and a flag hash as one record.
std::uint32_t BSLightingShaderMaterialEnvmap::ComputeCRC32(std::uint32_t a_flags)
{
    EnvmapCrcRecord record;
    if (textureSet._ptr) {
        CRC32Calculator::SizeOf32(&record.ids[0], textureSet._ptr->Unk_25(4), 0);
        CRC32Calculator::SizeOf32(&record.ids[1], textureSet._ptr->Unk_25(5), 0);
    }
    else {
        record.ids[0] = 0;
        record.ids[1] = 0;
    }
    record.unkB0 = unkB0;
    record.flagHash = ComputeFlagHash(a_flags);
    std::uint32_t out[2];
    CRC32Calculator::SizeOfSize(out, &record, 0x10);
    return out[0];
}

// Retained generated leaf; its byte-match evidence is renewed with this unit.
// GetFeature: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
BSShaderMaterial::Feature BSLightingShaderMaterialEnvmap::GetFeature() const
{
    return static_cast<Feature>(0x1);
}
