// BGSOpenCloseForm declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsopencloseform
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BGSOpenCloseForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSOpenCloseForm::Unk_03, BGSOpenCloseForm::HandleClose, BGSOpenCloseForm::HandleOpen: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); Unk_03 returns bool in the listing, the community declaration says void
// TESObjectREFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>

class TESObjectREFR;

class BGSOpenCloseForm
{
public:
    virtual bool Unk_03();  // compared: 0x267670
    virtual void HandleClose(TESObjectREFR* a_target, TESObjectREFR* a_activator);  // compared: 0x2677e0
    virtual void HandleOpen(TESObjectREFR* a_target, TESObjectREFR* a_activator);  // compared: 0x2677f0
};
static_assert(sizeof(BGSOpenCloseForm) == 0x8, "BGSOpenCloseForm size");
