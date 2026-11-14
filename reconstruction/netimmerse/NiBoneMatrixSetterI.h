// NiBoneMatrixSetterI declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nibonematrixsetteri
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// NiBoneMatrixSetterI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiBoneMatrixSetterI::~NiBoneMatrixSetterI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class NiBoneMatrixSetterI
{
public:
    NiBoneMatrixSetterI();
    virtual ~NiBoneMatrixSetterI() {}  // compared: 0x15797a0 (scalar deleting destructor)
};
static_assert(sizeof(NiBoneMatrixSetterI) == 0x8, "NiBoneMatrixSetterI size");
