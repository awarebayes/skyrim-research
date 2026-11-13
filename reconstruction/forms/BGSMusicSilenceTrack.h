// BGSMusicSilenceTrack declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bgsmusicsilencetrack
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Base form: local stand-ins (no ancestor has a shared header).
// BGSMusicSilenceTrack: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// GetDurationImpl, DoFinish, DoPause, DoUpdate, DoPlay, Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// duration, pad24, playTime, pauseTime: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the community comment marks duration as the FLTV subrecord
// BSIMusicTrack, BSIMusicTrack::MUSIC_STATUS, trackStatus, pad0C, GetType, GetMusicStatus, TestCanPlay, DoUpdate, DoPlay, DoPause, DoFinish, GetDurationImpl: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the base virtual slots are declared in NG's order up to slot 8, which the listings call through
// BGSMusicTrack: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the NG size 0x20 is kept, its members are not declared
// TESFile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); GetCurrentSubRecordType, ReadData, SeekNextSubrecord are NG names
// TESFile::unk000, TESFile::unk2E9, BGSMusicTrack::unk10, BSIMusicTrack::unk00, HandleSubrecord, LoadSubrecord: GUESS(low); the byte at 0x2E9 is a flag Load tests, the free helpers are called with this and the file
// GetTickCount: OBSERVED; the Windows import the listings call through the import table
// BSIMusicTrack::~BSIMusicTrack, unknown08: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class TESFile;
class BGSMusicSilenceTrack;

// GetTickCount: OBSERVED; the Windows API function the image imports
extern "C" __declspec(dllimport) std::uint32_t GetTickCount();

// TESFile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the three methods Load calls and the flag byte at 0x2E9 are declared
class TESFile
{
public:
    std::uint32_t GetCurrentSubRecordType();  // 0x1cdc10
    bool          ReadData(void* a_buf, std::uint32_t a_size);  // 0x1cdd10
    bool          SeekNextSubrecord();  // 0x1cdc60

    // unk000: GUESS(low); padding up to the flag byte
    std::uint8_t unk000[0x2E9];  // 000
    // unk2E9: GUESS(low); the flag that Load tests before it byte-swaps the duration
    std::uint8_t unk2E9;  // 2E9
};

// HandleSubrecord, LoadSubrecord: GUESS(low); the image calls them with the track and a subrecord type or the file
bool HandleSubrecord(BGSMusicSilenceTrack* a_track, std::uint32_t a_type);
void LoadSubrecord(BGSMusicSilenceTrack* a_track, TESFile* a_mod);

// BSIMusicTrack: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the virtual slots are in NG's order, only the members the compared code uses are declared
class BSIMusicTrack
{
public:
    enum class MUSIC_STATUS : std::uint32_t
    {
        kInactive = 0,
        kPlaying = 1,
        kPaused = 2,
        kFinishing = 3,
        kFinished = 4
    };

    virtual ~BSIMusicTrack() = default;                              // 00
    virtual void         DoUpdate();                                 // 01
    virtual void         DoPlay();                                   // 02
    virtual void         DoPause();                                  // 03
    virtual void         DoFinish(bool a_arg1, float a_arg2);        // 04
    virtual float        GetDurationImpl() const;                    // 05
    virtual std::uint32_t GetType() const;                           // 06
    virtual bool         TestCanPlay() const;                        // 07
    virtual MUSIC_STATUS GetMusicStatus() const;                     // 08

    // trackStatus: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    MUSIC_STATUS trackStatus;  // 08
    // pad0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint32_t pad0C;  // 0C
};
static_assert(sizeof(BSIMusicTrack) == 0x10, "BSIMusicTrack size");

// BGSMusicTrack: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG size 0x20, members not declared
class BGSMusicTrack : public BSIMusicTrack
{
public:
    // unk10: GUESS(low); bytes up to the NG size of 0x20
    std::uint8_t unk10[0x10];  // 10
};
static_assert(sizeof(BGSMusicTrack) == 0x20, "BGSMusicTrack size");

class BGSMusicSilenceTrack : public BGSMusicTrack
{
public:
    virtual float GetDurationImpl() const;  // compared: 0x325bc0
    virtual void DoFinish(bool a_arg1, float a_arg2);  // compared: 0x325b80
    virtual void DoPause();  // compared: 0x325b50
    virtual void DoPlay();  // compared: 0x325af0
    virtual void Load(TESFile* a_mod);  // compared: 0x3259f0

    // duration: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the FLTV subrecord value in seconds
    float duration;  // 20
    // pad24: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    std::uint32_t pad24;  // 24
    // playTime: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); GetTickCount stamp when playback started
    std::uint64_t playTime;  // 28
    // pauseTime: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); GetTickCount stamp when playback paused
    std::uint64_t pauseTime;  // 30
};
static_assert(sizeof(BGSMusicSilenceTrack) == 0x38, "BGSMusicSilenceTrack size");
