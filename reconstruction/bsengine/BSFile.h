// BSFile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s05-nibinarystream-bsfile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiFile.h for NiFile.
// BSFile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSFile::~BSFile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown48: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiFile.h"

class BSFile : public NiFile
{
public:
    BSFile();
    virtual ~BSFile();  // compared: 0xebeb10 (scalar deleting destructor)

    std::uint8_t unknown48[0x138];  // 48
};
static_assert(sizeof(BSFile) == 0x180, "BSFile size");
