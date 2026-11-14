// Origin: original reconstruction
// BGSAssociationType declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsassociationtype
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSAssociationType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSAssociationType::~BGSAssociationType, BGSAssociationType::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value, names, flags: GUESS(low); pooled string values and association flags.
class BSFixedString {
public:
    BSFixedString(const char* = nullptr);
    ~BSFixedString();
    BSFixedString& operator=(const BSFixedString&);
    const char* value;
};
class BGSAssociationType : public TESForm
{
public:
    BGSAssociationType();
    virtual ~BGSAssociationType();  // compared: 0x389800 (scalar deleting destructor)
    BSFixedString names[4];
    std::uint32_t flags;
    virtual void InitializeData();  // compared: 0x389430
};
