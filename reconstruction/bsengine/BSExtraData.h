// BSExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSExtraData::IsNotEqual, BSExtraData::~BSExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSExtraData
{
public:
    BSExtraData();
    virtual bool IsNotEqual(const BSExtraData* a_rhs) const;  // compared: 0x1565d0
    virtual ~BSExtraData() {}  // compared: 0x156400 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(BSExtraData) == 0x10, "BSExtraData size");
