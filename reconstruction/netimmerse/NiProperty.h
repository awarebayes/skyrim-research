// NiProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s04-niobject-niproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiObjectNET.h for NiObjectNET.
// NiProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiProperty::~NiProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObjectNET.h"

class NiProperty : public NiObjectNET
{
public:
    NiProperty();
    virtual ~NiProperty();  // compared: 0x20b410 (scalar deleting destructor); declared only, rule 18
};
static_assert(sizeof(NiProperty) == 0x30, "NiProperty size");
