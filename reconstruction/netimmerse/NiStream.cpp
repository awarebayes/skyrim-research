// NiStream functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nistream
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611131358-2).
// Compared functions:
//   RVA 0xee4710, 3 bytes: NiStream::Unk_07
//   RVA 0xee4350, 42 bytes: NiStream::Save1
//   RVA 0xee9550, 52 bytes: NiStream::~NiStream
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiStream.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared.
NiStream::NiStream()
{
}

// Unk_07: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void NiStream::Unk_07()
{
}

// Save1: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void NiStream::Save1(NiBinaryStream* a_stream)
{
    streamPtr2A0 = a_stream;
    Unk_10();
    streamPtr2A0 = nullptr;
}
