// BSISoundOutputModel declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsisoundoutputmodel
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSISoundOutputModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSISoundOutputModel::~BSISoundOutputModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class BSISoundOutputModel
{
public:
    BSISoundOutputModel();
    virtual ~BSISoundOutputModel();  // compared: 0x32baa0 (scalar deleting destructor)
};
static_assert(sizeof(BSISoundOutputModel) == 0x8, "BSISoundOutputModel size");
