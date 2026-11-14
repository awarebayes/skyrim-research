// BSISoundCategory declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsisoundcategory
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSISoundCategory: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSISoundCategory::~BSISoundCategory: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class BSISoundCategory
{
public:
    BSISoundCategory();
    virtual ~BSISoundCategory();  // compared: 0x329dc0 (scalar deleting destructor)
};
static_assert(sizeof(BSISoundCategory) == 0x8, "BSISoundCategory size");
