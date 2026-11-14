// TESChildCell declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-teschildcell
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// TESChildCell: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESChildCell::~TESChildCell: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class TESChildCell
{
public:
    TESChildCell();
    virtual ~TESChildCell();  // compared: 0x2b6290 (scalar deleting destructor)
};
static_assert(sizeof(TESChildCell) == 0x8, "TESChildCell size");
