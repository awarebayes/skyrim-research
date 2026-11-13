// BSAudio declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s15-bsaudio-bsaudio
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSAudio: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSAudio::Shutdown, BSAudio::Init, BSAudio::GetReceiver: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// BSAudioMonitor, BSAudioMonitor::Receiver: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// REX::W32::HWND: GUESS(low)
// BSAudioMonitor::Receiver::value, g_bsAudioDefaultReceiver: GUESS(low)
// field08, unknown09: GUESS(low)
#pragma once

#include <cstdint>

namespace REX
{
    namespace W32
    {
        struct HWND;
    }
}

class BSAudioMonitor
{
public:
    class Receiver
    {
    public:
        Receiver() {}

        std::uint64_t value;
    };
};

extern BSAudioMonitor::Receiver g_bsAudioDefaultReceiver;

class BSAudio
{
public:
    virtual void Shutdown();  // compared: 0xcd4b70
    virtual bool Init(REX::W32::HWND* a_wnd);  // compared: 0xcd4b60
    virtual BSAudioMonitor::Receiver GetReceiver(std::uint32_t a_monitor);  // compared: 0xcd4c20

    bool field08;  // 08
    std::uint8_t unknown09[0xF];  // 09
};
static_assert(sizeof(BSAudio) == 0x18, "BSAudio size");
