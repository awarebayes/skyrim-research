// BGSMoviePlayer declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsmovieplayer
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSMoviePlayer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// MoviePlayer: STANDIN EXE_RTTI
// BGSMoviePlayer::Unk_06, BGSMoviePlayer::Unk_05, BGSMoviePlayer::Unk_0A: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MoviePlayer::~MoviePlayer, unknown08, unknown58: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class MoviePlayer
{
public:
    virtual ~MoviePlayer() = default;
    std::uint8_t unknown08[0x50];  // 08
};
static_assert(sizeof(MoviePlayer) == 0x58, "MoviePlayer size");

// g_bgsMoviePlayerUnk: GUESS(low); the dword at RVA 0x33363c8 that Unk_0A returns.
extern std::uint32_t g_bgsMoviePlayerUnk;

class BGSMoviePlayer : public MoviePlayer
{
public:
    virtual void Unk_06();  // compared: 0x645120
    virtual void Unk_05();  // compared: 0x645130
    virtual std::uint32_t Unk_0A();  // compared: 0x644920

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown58[0x68];  // 58
};
static_assert(sizeof(BGSMoviePlayer) == 0xC0, "BGSMoviePlayer size");
