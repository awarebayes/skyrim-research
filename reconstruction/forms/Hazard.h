// Hazard declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-hazard
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// Hazard: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObjectREFR: STANDIN EXE_RTTI
// Hazard::Unk_A3, Hazard::OnAddCellPerformQueueReference, Hazard::IsPermanent: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// TESObjectCELL: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

class TESObjectCELL;

class TESObjectREFR : public TESForm
{
public:
};

class Hazard : public TESObjectREFR
{
public:
    void Unk_A3();  // compared: 0x7ee090
    virtual bool OnAddCellPerformQueueReference(TESObjectCELL& a_cell) const;  // compared: 0x7ee9c0
    bool IsPermanent() const;  // compared: 0x7ee8d0
};
