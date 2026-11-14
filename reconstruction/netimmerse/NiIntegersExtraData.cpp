// NiIntegersExtraData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-niintegersextradata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf12b50, 8 bytes: NiIntegersExtraData::GetRTTI
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiIntegersExtraData.h"

// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; only the name pointer
class NiRTTI
{
public:
    const char* name;  // 00
};

// NiRTTI_NiIntegersExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
const NiRTTI NiRTTI_NiIntegersExtraData{};

// RVA 0xf12b50, 8 bytes, NiIntegersExtraData::GetRTTI.
const NiRTTI* NiIntegersExtraData::GetRTTI() const
{
    return &NiRTTI_NiIntegersExtraData;
}
