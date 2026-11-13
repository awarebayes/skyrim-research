// NiFile declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s05-nibinarystream-nifile
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiBinaryStream.h for NiBinaryStream.
// NiFile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiFile::good: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown20: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiBinaryStream.h"

class NiFile : public NiBinaryStream
{
public:
    virtual bool good() const;  // compared: 0xeaf5b0

    std::uint8_t unknown20[0x24];  // 20
    // good44: GUESS(low)
    bool good44;  // 44
    std::uint8_t unknown45[0x3];  // 45
};
static_assert(sizeof(NiFile) == 0x48, "NiFile size");
