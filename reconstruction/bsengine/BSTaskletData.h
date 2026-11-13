// BSTaskletData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s16-bstaskletdata-bstaskletdata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSTaskletData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSTaskletData::~BSTaskletData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSTaskletData
{
public:
    BSTaskletData();
    virtual ~BSTaskletData();  // compared: 0x3fb670 (scalar deleting destructor); declared only, rule 18

    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(BSTaskletData) == 0x10, "BSTaskletData size");
