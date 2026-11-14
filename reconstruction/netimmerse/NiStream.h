// NiStream declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-nistream
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// NiStream: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiStream::Unk_07, NiStream::Save1, NiStream::~NiStream: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk01..unk0F, Unk_10: GUESS(low); placeholder vtable slots that put Unk_10 at slot 16 (offset 0x80), the slot Save1 calls
// streamPtr2A0, unk08, unk2A8: GUESS(low); the pointer at 0x2A0 that Save1 sets and clears; padding otherwise
// the complete destructor ??1NiStream: GUESS(low); declared only, bound by address through bind-hints.json
#pragma once

#include <cstdint>
#include <cstddef>

class NiBinaryStream;

class NiStream
{
public:
    NiStream();
    virtual ~NiStream();  // compared: 0xee9550 (scalar deleting destructor; the listing calls the complete destructor)

    // unk01..unk0F: GUESS(low); placeholder slots, only their order matters
    virtual void unk01();
    virtual void unk02();
    virtual void unk03();
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void Unk_07();  // compared: 0xee4710
    virtual void unk08();
    virtual void unk09();
    virtual void unk0A();
    virtual void unk0B();
    virtual void unk0C();
    virtual void unk0D();
    virtual void unk0E();
    virtual void unk0F();
    virtual void Unk_10();  // slot 16 (offset 0x80), called by Save1

    // Save1: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    void Save1(NiBinaryStream* a_stream);  // compared: 0xee4350

    // unkBlock08: GUESS(low); members before the pointer at 0x2A0 not recovered
    std::uint8_t unkBlock08[0x298];  // 08
    // streamPtr2A0: GUESS(low); set to the argument for the duration of the virtual call in Save1
    NiBinaryStream* streamPtr2A0;  // 2A0
    // unk2A8: GUESS(low); padding up to the 0x620 size
    std::uint8_t unk2A8[0x620 - 0x2A8];  // 2A8
};
static_assert(sizeof(NiStream) == 0x620, "NiStream size");
