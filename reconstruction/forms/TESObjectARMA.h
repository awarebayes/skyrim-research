// TESObjectARMA declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s06-tesobject-tesobjectarma
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESObjectARMA: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject: STANDIN EXE_RTTI
// TESObjectARMA::~TESObjectARMA: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESObject : public TESForm
{
public:
};

// TESRaceForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESRaceForm : public BaseFormComponent
{
public:
    virtual ~TESRaceForm();
    void* race;
};

// BGSBipedObjectForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class BGSBipedObjectForm : public BaseFormComponent
{
public:
    virtual ~BGSBipedObjectForm();
    std::uint64_t bipedModelData;
};

class TESObjectARMA : public TESObject, public TESRaceForm, public BGSBipedObjectForm
{
public:
    TESObjectARMA();
    virtual ~TESObjectARMA();  // compared: 0x27d3f8
};
