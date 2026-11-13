// BSAudio functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s15-bsaudio-bsaudio
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xcd4b70, 5 bytes: BSAudio::Shutdown
//   RVA 0xcd4b60, 7 bytes: BSAudio::Init
//   RVA 0xcd4c20, 14 bytes: BSAudio::GetReceiver
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSAudio.h"

void BSAudio::Shutdown()
{
    field08 = false;
}

bool BSAudio::Init(REX::W32::HWND* a_wnd)
{
    field08 = true;
    return true;
}

BSAudioMonitor::Receiver BSAudio::GetReceiver(std::uint32_t a_monitor)
{
    BSAudioMonitor::Receiver result = g_bsAudioDefaultReceiver;
    return result;
}
