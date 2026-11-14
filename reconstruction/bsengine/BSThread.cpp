// BSThread functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsthread
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611131358-4), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x60f1d0, 3 bytes: BSThread::Unk_02
//   RVA 0xceb190, 3 bytes: BSThread::Unk_01
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSThread.h"

// Body done: RVA 0x60f1d0, 3 bytes, BSThread::Unk_02.
void BSThread::Unk_02()
{
}

// Body done: RVA 0xceb190, 3 bytes, BSThread::Unk_01.
std::uint32_t BSThread::Unk_01()
{
    return 0;
}
