// BSNavmeshInfoMap declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s32-bstsingletonexplicit-vbsnav-bsnavmeshinfomap
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSNavmeshInfoMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSNavmeshInfoMap::~BSNavmeshInfoMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

// bsNavmeshInfoMapInstance: GUESS(low); the global pointer at RVA 0x31ecc58, bound by the unit's bind-hints.json
extern "C" void* bsNavmeshInfoMapInstance;

class BSNavmeshInfoMap
{
public:
    BSNavmeshInfoMap();
    virtual ~BSNavmeshInfoMap();  // compared: 0x11f01d0 (scalar deleting destructor)
};
static_assert(sizeof(BSNavmeshInfoMap) == 0x8, "BSNavmeshInfoMap size");
