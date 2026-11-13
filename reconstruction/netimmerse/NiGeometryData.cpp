// NiGeometryData functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-nigeometrydata
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xefbff0, 5 bytes: NiGeometryData::GetActiveVertexCount
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiGeometryData.h"

// TODO body: RVA 0xefbff0, 5 bytes, NiGeometryData::GetActiveVertexCount.
std::uint16_t NiGeometryData::GetActiveVertexCount() const
{
    return activeVertexCount;
}
