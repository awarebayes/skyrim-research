// MagicItemData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-magicitemdata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// MagicItemData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// MagicItemData::GetCount, MagicItemData::GetEnabled: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown08: GUESS(low)
// data18: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class MagicItemData
{
public:
    virtual std::uint32_t GetCount();  // compared: 0x956d90
    virtual bool GetEnabled();  // compared: 0x951e80

    // Padding up to the pointer read by GetEnabled at offset 0x18.
    std::uint8_t unknown08[0x10];  // 08
    void* data18;  // 18
};
static_assert(sizeof(MagicItemData) == 0x20, "MagicItemData size");
