// BGSEntryPointFunctionData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s07-bgsentrypointfunctiondata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x38e0c0, 6 bytes: BGSEntryPointFunctionData::Unk_05
//   RVA 0x38ebb0, 43 bytes: BGSEntryPointFunctionData::~BGSEntryPointFunctionData
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSEntryPointFunctionData.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSEntryPointFunctionData::BGSEntryPointFunctionData()
{
}

// TODO body: RVA 0x38e0c0, 6 bytes, BGSEntryPointFunctionData::Unk_05.
std::uint16_t BGSEntryPointFunctionData::Unk_05()
{
    return 0xffff;
}

BGSEntryPointFunctionData::~BGSEntryPointFunctionData()
{
}
