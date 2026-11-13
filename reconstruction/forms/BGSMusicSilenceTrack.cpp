// BGSMusicSilenceTrack functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bgsmusicsilencetrack
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (worker haiku-202611122314-2).
// Compared functions:
//   RVA 0x325bc0, 6 bytes: BGSMusicSilenceTrack::GetDurationImpl
//   RVA 0x325b80, 8 bytes: BGSMusicSilenceTrack::DoFinish
//   RVA 0x325b50, 34 bytes: BGSMusicSilenceTrack::DoPause
//   RVA 0x325af0, 90 bytes: BGSMusicSilenceTrack::DoPlay
//   RVA 0x3259f0, 147 bytes: BGSMusicSilenceTrack::Load
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSMusicSilenceTrack.h"

// RVA 0x325bc0, 6 bytes
float BGSMusicSilenceTrack::GetDurationImpl() const
{
    return duration;
}

// RVA 0x325b80, 8 bytes
void BGSMusicSilenceTrack::DoFinish(bool a_arg1, float a_arg2)
{
    trackStatus = MUSIC_STATUS::kFinished;
}

// RVA 0x325b50, 34 bytes
void BGSMusicSilenceTrack::DoPause()
{
    pauseTime = GetTickCount();
    trackStatus = MUSIC_STATUS::kPaused;
}

// RVA 0x325af0, 90 bytes
void BGSMusicSilenceTrack::DoPlay()
{
    std::uint32_t now = GetTickCount();
    if (GetMusicStatus() == MUSIC_STATUS::kPaused) {
        playTime = (playTime - pauseTime) + now;
        trackStatus = MUSIC_STATUS::kPlaying;
        return;
    }
    playTime = now;
    trackStatus = MUSIC_STATUS::kPlaying;
}

// RVA 0x3259f0, 147 bytes
void BGSMusicSilenceTrack::Load(TESFile* a_mod)
{
    std::uint32_t type = a_mod->GetCurrentSubRecordType();
    while (type != 0) {
        if (HandleSubrecord(this, type)) {
            LoadSubrecord(this, a_mod);
        } else if (type == 0x56544c46) {
            a_mod->ReadData(&duration, 4);
            if (a_mod->unk2E9 != 0) {
                std::uint32_t& bits = *reinterpret_cast<std::uint32_t*>(&duration);
                bits = (bits >> 24) | ((bits & 0xFF0000) >> 8) | ((bits & 0xFF00) << 8) | (bits << 24);
            }
        }
        if (!a_mod->SeekNextSubrecord()) {
            break;
        }
        type = a_mod->GetCurrentSubRecordType();
    }
}
