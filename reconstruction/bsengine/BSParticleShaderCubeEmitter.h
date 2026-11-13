// BSParticleShaderCubeEmitter declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsparticleshadercubeemitter
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiRefObject.h for NiRefObject.
// BSParticleShaderCubeEmitter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSParticleShaderEmitter: STANDIN EXE_RTTI
// BSParticleShaderCubeEmitter::~BSParticleShaderCubeEmitter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown10, unknownED0: GUESS(low)
// Generate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); signature from the sheet, not checked against the community header
#pragma once

#include <cstdint>
#include "../netimmerse/NiRefObject.h"

class NiPoint3;

class BSParticleShaderEmitter : public NiRefObject
{
public:
    std::uint8_t unknown10[0xEC0];  // 10
};
static_assert(sizeof(BSParticleShaderEmitter) == 0xED0, "BSParticleShaderEmitter size");

class BSParticleShaderCubeEmitter : public BSParticleShaderEmitter
{
public:
    BSParticleShaderCubeEmitter();
    virtual bool Generate(bool a_arg1, NiPoint3& a_arg2, NiPoint3& a_arg3);
    virtual ~BSParticleShaderCubeEmitter();  // compared: 0x2a0b60 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknownED0[0x110];  // ED0
};
static_assert(sizeof(BSParticleShaderCubeEmitter) == 0xFE0, "BSParticleShaderCubeEmitter size");
