// NiFloatsExtraData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nifloatsextradata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf119b0, 8 bytes: NiFloatsExtraData::GetRTTI
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiFloatsExtraData.h"

// NiRTTI_NiFloatsExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
extern const NiRTTI NiRTTI_NiFloatsExtraData;

// TODO body: RVA 0xf119b0, 8 bytes, NiFloatsExtraData::GetRTTI.
const NiRTTI* NiFloatsExtraData::GetRTTI() const
{
    return &NiRTTI_NiFloatsExtraData;
}
