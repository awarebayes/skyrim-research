// BGSBaseAlias functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsbasealias
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-1), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x392c60, 66 bytes: BGSBaseAlias::~BGSBaseAlias
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSBaseAlias.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSBaseAlias::BGSBaseAlias()
{
}

// TODO body: RVA 0x392c60, 66 bytes, BGSBaseAlias::~BGSBaseAlias; compared as the scalar deleting
// destructor. If the target calls a separate destructor, keep only the declaration and delete this
// definition (cookbook rule 18).
// ~BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); releases the member block, then the object is freed by the deleting form.
BGSBaseAlias::~BGSBaseAlias()
{
    AliasMemberCleanupStub(&unknown08);
}
