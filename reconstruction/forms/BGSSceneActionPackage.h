// BGSSceneActionPackage declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneactionpackage
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/BGSSceneAction.h for BGSSceneAction (size 0xA0, so this class
// adds no members; the dword at 0x20 lies in the base and is reached through RawAt).
// BGSSceneActionPackage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSSceneActionPackage::Unk_0B, BGSSceneActionPackage::Unk_11: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// RawAt: GUESS(low)
#pragma once

#include <cstddef>
#include <cstdint>
#include "../forms/BGSSceneAction.h"

template <class T>
T& RawAt(const void* a_base, std::ptrdiff_t a_offset)
{
    return *reinterpret_cast<T*>(const_cast<std::uint8_t*>(reinterpret_cast<const std::uint8_t*>(a_base)) + a_offset);
}

class BGSSceneActionPackage : public BGSSceneAction
{
public:
    virtual void Unk_0B();  // compared: 0x3ac610
    virtual void Unk_11();  // compared: 0x3ac2b0
};
