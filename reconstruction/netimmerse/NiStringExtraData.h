// NiStringExtraData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nistringextradata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// NiStringExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiStringExtraData::IsEqual, NiStringExtraData::LoadBinary, NiStringExtraData::RegisterStreamables: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiExtraData.h"

class NiStringExtraData : public NiExtraData
{
public:
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xef71c0
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xef70e0
    virtual bool RegisterStreamables(NiStream& a_stream);  // compared: 0xef7130

    BSFixedString value;  // 18
};
static_assert(sizeof(NiStringExtraData) == 0x20, "NiStringExtraData size");
