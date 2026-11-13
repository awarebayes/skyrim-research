// BGSVolumetricLighting declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgsvolumetriclighting
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSVolumetricLighting: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSVolumetricLighting::~BGSVolumetricLighting: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class BGSVolumetricLighting : public TESForm
{
public:
    BGSVolumetricLighting();
    virtual ~BGSVolumetricLighting();  // compared: 0x263d40 (scalar deleting destructor)

    // unknown20: GUESS(low); the padding to the size the sized operator delete receives
    std::uint8_t unknown20[0x30];  // 20
};
static_assert(sizeof(BGSVolumetricLighting) == 0x50, "BGSVolumetricLighting size");
