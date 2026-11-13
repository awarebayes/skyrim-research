// BGSMusicPaletteTrack functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bgsmusicpalettetrack
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x325550, 6 bytes: BGSMusicPaletteTrack::GetDurationImpl
//   RVA 0x325570, 47 bytes: BGSMusicPaletteTrack::GetType
//   RVA 0x325000, 114 bytes: BGSMusicPaletteTrack::DoPause
//   RVA 0x325080, 136 bytes: BGSMusicPaletteTrack::DoFinish
//   RVA 0x324f00, 243 bytes: BGSMusicPaletteTrack::DoPlay
//   RVA 0x324d80, 367 bytes: BGSMusicPaletteTrack::DoUpdate
//   RVA 0x324bd0, 417 bytes: BGSMusicPaletteTrack::InitItem
// Adapted bodies: none
// Set aside in .local/tasks/p46-n-bgsmusicpalettetrack/near-miss/: DoPlay (0x324f00), DoUpdate (0x324d80), InitItem (0x324bd0)
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSMusicPaletteTrack.h"

// RVA 0x325550, 6 bytes
float BGSMusicPaletteTrack::GetDurationImpl() const
{
    return m_duration;
}

// RVA 0x325570, 47 bytes: the type id is registered on first use.
TrackType BGSMusicPaletteTrack::GetType() const
{
    if (g_paletteTrackTypeId == 0) {
        RegisterTrackType(&g_paletteTrackTypeId, "BGSMusicPaletteTrack", 0);
    }
    return static_cast<TrackType>(g_paletteTrackTypeId);
}

// RVA 0x325000, 114 bytes: every selected item is paused, then the time of the pause is kept.
void BGSMusicPaletteTrack::DoPause()
{
    for (std::uint32_t i = 0; i < 3; ++i) {
        if (m_indices[i] >= 0) {
            reinterpret_cast<PaletteItem*>(m_items[i].data[static_cast<std::uint32_t>(m_indices[i])])->Pause();
        }
    }
    m_pauseStart = GetTickCount();
    m_state = 2;
}

// RVA 0x325080, 136 bytes: every selected item finishes with the flag and the float.
void BGSMusicPaletteTrack::DoFinish(bool a_arg1, float a_arg2)
{
    for (std::uint32_t i = 0; i < 3; ++i) {
        if (m_indices[i] >= 0) {
            reinterpret_cast<PaletteItem*>(m_items[i].data[static_cast<std::uint32_t>(m_indices[i])])->Finish(a_arg1, a_arg2);
        }
    }
    m_state = 3;
}
