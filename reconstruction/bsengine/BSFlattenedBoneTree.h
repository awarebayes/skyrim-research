// BSFlattenedBoneTree declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-bsflattenedbonetree
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiNode.h for NiNode.
// BSFlattenedBoneTree: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSFlattenedBoneTree::UpdateDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// UpdateBoneRoots: GUESS(low)
// unknown128: GUESS(low)
#pragma once

#include <cstdint>
#include "../netimmerse/NiNode.h"

class BSFlattenedBoneTree : public NiNode
{
public:
    virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xef4d10

    void UpdateBoneRoots();

    std::uint8_t unknown128[0x40];  // 128
};
static_assert(sizeof(BSFlattenedBoneTree) == 0x168, "BSFlattenedBoneTree size");
