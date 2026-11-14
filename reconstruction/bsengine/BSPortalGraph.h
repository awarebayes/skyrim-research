// BSPortalGraph declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsportalgraph
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiRefObject.h for NiRefObject.
// BSPortalGraph: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSPortalGraph::~BSPortalGraph: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiRefObject.h"

class BSPortalGraph : public NiRefObject
{
public:
    BSPortalGraph();
    virtual ~BSPortalGraph();  // compared: 0xfdb1b0 (scalar deleting destructor)

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown10[0xB8];  // 10
};
static_assert(sizeof(BSPortalGraph) == 0xC8, "BSPortalGraph size");
