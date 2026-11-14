// BSMaterialObject declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsmaterialobject
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSMaterialObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSMaterialObject::EnsureLoaded, BSMaterialObject::~BSMaterialObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSMaterialObject
{
public:
    BSMaterialObject();
    virtual void EnsureLoaded();  // compared: 0x1534210
    virtual ~BSMaterialObject();  // compared: 0x321da0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x50];  // 08
};
static_assert(sizeof(BSMaterialObject) == 0x58, "BSMaterialObject size");
