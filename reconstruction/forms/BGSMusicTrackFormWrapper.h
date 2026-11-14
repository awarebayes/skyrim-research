// BGSMusicTrackFormWrapper declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsmusictrackformwrapper
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSMusicTrackFormWrapper: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSMusicTrackFormWrapper::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSMusicTrackFormWrapper::~BGSMusicTrackFormWrapper: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); the compared thunk at RVA 0x327554 adjusts this by 0x20 and jumps to the complete destructor at RVA 0x327560, bound by hint
// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
// SetFormHelper: GUESS(low); the callee at RVA 0x1e60b0 taking the form and a bool, tail-called by InitItemImpl, bound by hint
// BGSMusicTrack, BGSMusicTrack::Slot00 through Slot0A: GUESS(low); placeholder slots so Slot0B lands on slot 11 (0x58)
// BGSMusicTrack::Slot0B: GUESS(low); the slot InitItemImpl calls with the wrapper as the argument
// BGSMusicTrackSecondary: GUESS(low); the secondary base at +0x20 whose destructor slot is the compared thunk
// unk08: GUESS(low); bytes between the vftable and the music track pointer
// musicTrack: GUESS(low); the pointer at wrapper +0x30 that InitItemImpl reads
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// SetFormHelper: GUESS(low); the callee at RVA 0x1e60b0 taking the form and a bool
void SetFormHelper(TESForm* a_form, bool a_set);

class BGSMusicTrack
{
public:
    virtual void Slot00();
    virtual void Slot01();
    virtual void Slot02();
    virtual void Slot03();
    virtual void Slot04();
    virtual void Slot05();
    virtual void Slot06();
    virtual void Slot07();
    virtual void Slot08();
    virtual void Slot09();
    virtual void Slot0A();
    virtual void Slot0B(TESForm* a_form);
};

class BGSMusicTrackSecondary
{
public:
    virtual ~BGSMusicTrackSecondary() {}  // 00
    std::uint8_t unk08[0x8];  // 08
    BGSMusicTrack* musicTrack;  // 10
};
static_assert(sizeof(BGSMusicTrackSecondary) == 0x18, "BGSMusicTrackSecondary size");

class BGSMusicTrackFormWrapper : public TESForm, public BGSMusicTrackSecondary
{
public:
    BGSMusicTrackFormWrapper();
    virtual void InitItemImpl();  // compared: 0x327430
    virtual ~BGSMusicTrackFormWrapper();  // compared: 0x327554
};
