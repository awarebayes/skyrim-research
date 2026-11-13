// BGSSceneAction functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneaction
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3ab090, 5 bytes: BGSSceneAction::Unk_0B
//   RVA 0x3ab120, 5 bytes: BGSSceneAction::Unk_10
//   RVA 0x3aaf60, 8 bytes: BGSSceneAction::ClearFlags
//   RVA 0x3ab130, 33 bytes: BGSSceneAction::Unk_11
//   RVA 0x3aaf20, 58 bytes: BGSSceneAction::Unk_02
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <atomic>

#include "BGSSceneAction.h"

// TODO body: RVA 0x3ab090, 5 bytes, BGSSceneAction::Unk_0B.
void BGSSceneAction::Unk_0B()
{
    flags14 &= 0xfc;
}

// TODO body: RVA 0x3ab120, 5 bytes, BGSSceneAction::Unk_10.
void BGSSceneAction::Unk_10()
{
    flags14 |= 1;
}

// TODO body: RVA 0x3aaf60, 8 bytes, BGSSceneAction::ClearFlags.
void BGSSceneAction::ClearFlags()
{
    flags10 = 0;
}

// TODO body: RVA 0x3ab130, 33 bytes, BGSSceneAction::Unk_11.
void BGSSceneAction::Unk_11()
{
    flags14 &= 0xfe;
    if (!Unk_05()) {
        flags14 |= 2;
    }
}

// TODO body: RVA 0x3aaf20, 58 bytes, BGSSceneAction::Unk_02.
void BGSSceneAction::Unk_02(BGSSceneAction* a_other)
{
    const auto flags = unknown08;
    unknown08 = FindSceneActionEntry(a_other->unknown98, flags) ? flags : 0xffffffff;
    std::atomic_signal_fence(std::memory_order_seq_cst);
}

bool BGSSceneAction::Unk_05()
{
    return false;
}
