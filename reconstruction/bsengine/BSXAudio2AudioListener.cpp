// BSXAudio2AudioListener functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s22-bsaudiolistener-bsxaudio2audiolistener
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xcd8c80, 10 bytes: BSXAudio2AudioListener::Unk_01
//   RVA 0xcd8da0, 35 bytes: BSXAudio2AudioListener::Unk_06
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSXAudio2AudioListener.h"

void BSXAudio2AudioListener::Unk_01()
{
    field58 = 0;
    field60 = 0;
}

void BSXAudio2AudioListener::Unk_06(const std::uint32_t* a_src)
{
    unk2C = a_src[0];
    unk30 = a_src[1];
    unk34 = a_src[2];
    field64 = a_src[0];
    field68 = a_src[2];
    field6C = a_src[1];
}
