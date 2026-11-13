// BGSMusicPaletteTrack declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bgsmusicpalettetrack
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSMusicPaletteTrack: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSIMusicTrack, BGSMusicTrack: STANDIN EXE_RTTI
// BGSMusicPaletteTrack::GetDurationImpl, BGSMusicPaletteTrack::GetType, BGSMusicPaletteTrack::DoPause, BGSMusicPaletteTrack::DoFinish, BGSMusicPaletteTrack::DoPlay, BGSMusicPaletteTrack::DoUpdate, BGSMusicPaletteTrack::InitItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TrackType, TESForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSIMusicTrack::~BSIMusicTrack, unknown0C: GUESS(low)
// GetTickCount: OBSERVED; the Windows import the listings call through the import table
// BSIMusicTrack::m_state: GUESS(low); the state word the track sets to 1 to 4
// Unk05, Unk06, Unk07: GUESS(low); placeholders for the item slots the listings do not call
// PaletteItem, PaletteItem::Update, PaletteItem::Play, PaletteItem::Pause, PaletteItem::Finish, PaletteItem::GetState: GUESS(low)
// PaletteVector, RegisterTrackType: GUESS(low)
// g_paletteTrackTypeId: GUESS(low); the type id GetType registers once, bound by the unit's bind-hints.json
// m_items, m_indices, m_duration, m_time78, m_playStart, m_pauseStart: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class TESForm;

enum class TrackType : std::uint32_t;

// GetTickCount: OBSERVED; the Windows API function the image imports
extern "C" __declspec(dllimport) std::uint32_t GetTickCount();

extern std::uint32_t g_paletteTrackTypeId;

class BSIMusicTrack
{
public:
    virtual ~BSIMusicTrack() = default;
    // m_state: GUESS(low); the state word the track sets to 1 to 4
    std::uint32_t m_state;         // 08
    std::uint8_t unknown0C[0x4];   // 0c
};
static_assert(sizeof(BSIMusicTrack) == 0x10, "BSIMusicTrack size");

class BGSMusicTrack : public BSIMusicTrack
{
public:
};

// PaletteItem: GUESS(low); the item objects a palette vector holds, slots 1 to 4 and 8 are the ones the listings call
class PaletteItem
{
public:
    virtual ~PaletteItem() = default;
    // Update: GUESS(low); slot 1
    virtual void Update();
    // Play: GUESS(low); slot 2
    virtual void Play();
    // Pause: GUESS(low); slot 3
    virtual void Pause();
    // Finish: GUESS(low); slot 4
    virtual void Finish(bool a_arg1, float a_arg2);
    // Unk05, Unk06, Unk07: GUESS(low); placeholders for the item slots the listings do not call
    virtual void Unk05();
    virtual void Unk06();
    virtual void Unk07();
    // GetState: GUESS(low); slot 8
    virtual std::int32_t GetState();
};

// PaletteVector: GUESS(low); one 0x18-byte list of items, the element is a handle or a pointer depending on the step
struct PaletteVector
{
    std::uint64_t* data;           // 00
    std::uint8_t unknown08[0x8];   // 08
    std::uint32_t count;           // 10
    std::uint8_t unknown14[0x4];   // 14
};
static_assert(sizeof(PaletteVector) == 0x18, "PaletteVector size");

// RegisterTrackType: GUESS(low)
void RegisterTrackType(std::uint32_t* a_slot, const char* a_name, std::uint32_t a_flags);

class BGSMusicPaletteTrack : public BGSMusicTrack
{
public:
    virtual float GetDurationImpl() const;  // compared: 0x325550
    virtual TrackType GetType() const;  // compared: 0x325570
    virtual void DoPause();  // compared: 0x325000
    virtual void DoFinish(bool a_arg1, float a_arg2);  // compared: 0x325080
    virtual void DoPlay();  // compared: 0x324f00
    virtual void DoUpdate();  // compared: 0x324d80
    virtual void InitItem(TESForm* a_form);  // compared: 0x324bd0
    // GetState: GUESS(low); slot 8 that the listings call on this
    virtual std::int32_t GetState();

    std::uint8_t unknown10[0x10];  // 10
    // m_items: GUESS(low); three lists, each 0x18 bytes
    PaletteVector m_items[3];  // 20
    // m_indices: GUESS(low); one selected index per list, negative when none
    std::int32_t m_indices[3];  // 68
    // m_duration: GUESS(low); returned by GetDurationImpl
    float m_duration;  // 74
    // m_time78: GUESS(low)
    float m_time78;  // 78
    std::uint32_t unknown7C;  // 7c
    // m_playStart: GUESS(low)
    std::uint64_t m_playStart;  // 80
    // m_pauseStart: GUESS(low)
    std::uint64_t m_pauseStart;  // 88
};
static_assert(sizeof(BGSMusicPaletteTrack) == 0x90, "BGSMusicPaletteTrack size");
