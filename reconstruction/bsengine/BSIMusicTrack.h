// BSIMusicTrack::TestCanPlay, build sse-steam-1-7-104, RVA 0x326f40, 3 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"medium","kind":"public","repository":"meh321/AddressLibraryDatabase","revision":"0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91","source":"meh321"},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// Task p92-s-bsimusictrack: DoClearDucking (0x325530), DoSetDuckingAttenuation (0x325540) and GetMusicStatus (0x325560) are added beside TestCanPlay.
// BSIMusicTrack: EXE_RTTI
// TestCanPlay: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// TestCanPlay: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class BSIMusicTrack
{
public:
    virtual std::uint8_t TestCanPlay() const;
    // DoClearDucking, DoSetDuckingAttenuation, GetMusicStatus: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    virtual void DoClearDucking();
    virtual void DoSetDuckingAttenuation(std::uint16_t a_ducking);
    virtual std::uint32_t GetMusicStatus() const;

    // musicStatus: GUESS(low); the dword at 0x8 that GetMusicStatus returns, name invented
    std::uint32_t musicStatus;
};
