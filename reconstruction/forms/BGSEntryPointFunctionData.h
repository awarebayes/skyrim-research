// BGSEntryPointFunctionData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s07-bgsentrypointfunctiondata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BGSEntryPointFunctionData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSEntryPointFunctionData::Unk_05, BGSEntryPointFunctionData::~BGSEntryPointFunctionData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

class BGSEntryPointFunctionData
{
public:
    BGSEntryPointFunctionData();
    virtual std::uint16_t Unk_05();  // compared: 0x38e0c0
    virtual ~BGSEntryPointFunctionData();  // compared: 0x38ebb0 (scalar deleting destructor)
};
static_assert(sizeof(BGSEntryPointFunctionData) == 0x8, "BGSEntryPointFunctionData size");
