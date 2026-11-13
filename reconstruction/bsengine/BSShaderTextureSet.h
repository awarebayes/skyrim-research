// BSShaderTextureSet declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsshadertextureset
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObject.h for NiObject.
// BSShaderTextureSet: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSTextureSet: STANDIN EXE_RTTI
// BSShaderTextureSet::GetTexturePath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// texturePaths: GUESS(low); element count is the padding that was split off, the target indexes it by Texture
// Texture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG nests it in BSTextureSet::Textures
// as std::uint32_t, signed here because the target sign-extends the index (MOVSXD)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObject.h"

enum Texture : std::int32_t
{
};

class BSTextureSet : public NiObject
{
public:
};
static_assert(sizeof(BSTextureSet) == 0x10, "BSTextureSet size");

class BSShaderTextureSet : public BSTextureSet
{
public:
    virtual const char* GetTexturePath(Texture a_texture);  // compared: 0x153b3c0

    // Path pointers, one per texture slot, read by index in GetTexturePath.
    const char* texturePaths[0x9];  // 10
};
static_assert(sizeof(BSShaderTextureSet) == 0x58, "BSShaderTextureSet size");
