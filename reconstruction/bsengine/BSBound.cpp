// BSBound functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsbound
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611131358-2).
// Compared functions:
//   RVA 0xff17c0, 55 bytes: BSBound::LoadBinary
//   RVA 0xff1760, 4 bytes: BSBound::CreateClone
//   RVA 0xff1b90, 8 bytes: BSBound::GetRTTI
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSBound.h"

// LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void BSBound::LoadBinary(NiStream& a_stream)
{
    NiExtraData::LoadBinary(a_stream);
    loaderA.Load(a_stream);
    loaderB.Load(a_stream);
}

// CreateClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
NiObject* BSBound::CreateClone(NiCloningProcess& a_cloning)
{
    return this;
}

// GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
const NiRTTI* BSBound::GetRTTI() const
{
    return &NiRTTI_BSBound;
}
