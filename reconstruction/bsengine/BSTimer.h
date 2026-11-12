// Type declarations for the BSTimer translation unit (build sse-steam-1-7-104).
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/B/BSTimer.h.
// Adapted bodies: none declared; tools/check_origin.py reports none above its threshold (0.75)
// at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// This is a minimal stand-in. All names are COMMUNITY (that revision, MIT) and unverified, except
// unk-prefixed members which are GUESS-free placeholders for unknown fields.
// Only the offsets the compared function touches (delta at 0x18, flag at 0x3A) are used.
#pragma once

#include <cstdint>

class BSTimer {
public:
    // COMMUNITY: BSTimer::SetGlobalTimeMultiplier
    void SetGlobalTimeMultiplier(float a_multiplier, bool a_arg2);

    // COMMUNITY: QGlobalTimeMultiplier / QGlobalTimeMultiplierTarget accessors in NG read these
    // globals. They are modelled here as static data; the map binds them to the image addresses.
    static float QGlobalTimeMultiplier;
    static float QGlobalTimeMultiplierTarget;

    std::uint64_t unk00;                          // 00
    std::uint32_t lastPerformanceCount;           // 08
    std::uint32_t pad0C;                          // 0C (GUESS: alignment padding)
    float         clamp;                          // 10
    float         clampRemainder;                 // 14
    float         delta;                          // 18
    float         realTimeDelta;                  // 1C
    std::uint32_t unk20;                          // 20
    std::uint32_t unk24;                          // 24
    float         unk28;                          // 28
    std::uint32_t unk2C;                          // 2C
    std::uint32_t unk30;                          // 30
    std::uint32_t unk34;                          // 34
    std::uint8_t  unk38;                          // 38
    std::uint8_t  unk39;                          // 39
    bool          useGlobalTimeMultiplierTarget;  // 3A
    std::uint8_t  pad3B;                          // 3B
    std::uint32_t pad3C;                          // 3C
};
