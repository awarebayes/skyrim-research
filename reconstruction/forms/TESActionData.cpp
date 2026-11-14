// TESActionData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesactiondata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// TESActionData::Unk_02: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// return type std::uint32_t is a guess; the listing returns 0 in EAX
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x78db50, 3 bytes: TESActionData::Unk_02
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESActionData.h"

// RVA 0x78db50, 3 bytes, TESActionData::Unk_02. Returns 0 in EAX.
std::uint32_t TESActionData::Unk_02()
{
    return 0;
}
