// BSWindModifier functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswindmodifier
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xfd8f90, 8 bytes: BSWindModifier::GetRTTI
//   RVA 0xfd8f50, 52 bytes: BSWindModifier::~BSWindModifier (declared in the header, not defined
//   here: the target calls the complete destructor, so attempt binds that call)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSWindModifier.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSWindModifier::BSWindModifier()
{
}

// NiRTTI_BSWindModifier: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
extern const NiRTTI NiRTTI_BSWindModifier;

const NiRTTI* BSWindModifier::GetRTTI() const
{
    return &NiRTTI_BSWindModifier;
}
