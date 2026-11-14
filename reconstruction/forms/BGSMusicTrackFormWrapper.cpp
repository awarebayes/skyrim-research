// BGSMusicTrackFormWrapper functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsmusictrackformwrapper
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x327430, 58 bytes: BGSMusicTrackFormWrapper::InitItemImpl
//   RVA 0x327554, 9 bytes: BGSMusicTrackFormWrapper::dtor
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSMusicTrackFormWrapper.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSMusicTrackFormWrapper::BGSMusicTrackFormWrapper()
{
}

// RVA 0x327430, 58 bytes: when flag bit 3 is clear and a music track is set, the track is
// notified and the form is set.
void BGSMusicTrackFormWrapper::InitItemImpl()
{
    if (!TestBit(formFlags, 3)) {
        if (musicTrack) {
            musicTrack->Slot0B(this);
            SetFormHelper(this, true);
        }
    }
}
