// NiTexture declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-nitexture
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObject.h for NiObject.
// NiTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiTexture::Unk_28, NiTexture::~NiTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// a_arg1, a_arg2, a_arg3, a_arg4: GUESS(low)
// unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObject.h"

class NiTexture : public NiObject
{
public:
    NiTexture();
    virtual void Unk_28(std::uint32_t& a_arg1, std::uint32_t& a_arg2, std::uint32_t& a_arg3, std::uint32_t& a_arg4);  // compared: 0xf05970
    // Keep the complete destructor as a separate call, matching the engine's out-of-line cleanup.
    __declspec(noinline) virtual ~NiTexture();  // compared: 0xef3ea0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown10[0x30];  // 10
};
static_assert(sizeof(NiTexture) == 0x40, "NiTexture size");
