// BSXFlags declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bsxflags
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiIntegerExtraData.h for NiIntegerExtraData.
// BSXFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSXFlags::CreateClone, BSXFlags::RegisterStreamables, BSXFlags::~BSXFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiObject, NiCloningProcess, NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiIntegerExtraData.h"

class NiObject;
class NiCloningProcess;
class NiStream;

class BSXFlags : public NiIntegerExtraData
{
public:
    BSXFlags();
    virtual NiObject* CreateClone(NiCloningProcess& a_cloning);  // compared: 0xfd2da0
    virtual bool RegisterStreamables(NiStream& a_stream);  // compared: 0xfd2de0
    virtual ~BSXFlags();  // compared: 0xfd30c0 (scalar deleting destructor)
};
static_assert(sizeof(BSXFlags) == 0x20, "BSXFlags size");
