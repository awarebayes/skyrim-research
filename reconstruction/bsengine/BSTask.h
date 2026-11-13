// BSTask declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s33-bstask-bstask
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSTask: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSTask::GetDescription, BSTask::~BSTask: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown08: GUESS(low)
#pragma once

#include <cstdint>

class BSTask
{
public:
    BSTask();
    virtual bool GetDescription(char* a_dest, std::uint32_t a_maxCount);  // compared: 0xfc26e0
    virtual ~BSTask();  // compared: 0x19be50 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown08[0x10];  // 08
};
static_assert(sizeof(BSTask) == 0x18, "BSTask size");
