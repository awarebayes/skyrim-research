// BGSScene declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsscene
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSScene: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSScene::~BGSScene: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class BGSScene : public TESForm
{
public:
    BGSScene();
    virtual ~BGSScene();  // compared: 0x3aa560 (scalar deleting destructor); declared only, rule 18

    // unknown20: GUESS(low); the padding to the size the sized operator delete receives
    std::uint8_t unknown20[0xA8];  // 20
};
static_assert(sizeof(BGSScene) == 0xC8, "BGSScene size");
