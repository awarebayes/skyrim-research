// TESObjectLIGH functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tesobjectligh
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x275080, 20 bytes: TESObjectLIGH::Activate
//   RVA 0x275210, 46 bytes: TESObjectLIGH::SaveGame
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectLIGH.h"

// Body done: RVA 0x275080, 20 bytes, TESObjectLIGH::Activate. The fallback is a tail call in the
// target when the flag is set, and false otherwise.
bool TESObjectLIGH::Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t a_targetCount)
{
    if (!TestBit(unknownEC, 1)) {
        return false;
    }
    return TESBoundObject::Activate(a_targetRef, a_activatorRef, a_arg3, a_object, a_targetCount);
}

// Body done: RVA 0x275210, 46 bytes, TESObjectLIGH::SaveGame. The base save runs first; the
// sub-object save is the last call, a tail call in the target.
void TESObjectLIGH::SaveGame(BGSSaveFormBuffer* a_buf)
{
    TESForm::SaveGame(a_buf);
    SaveValueState(unknownB0, a_buf);
}
