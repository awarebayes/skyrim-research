// Origin: original reconstruction
// BGSOutfit declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsoutfit
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSOutfit: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSOutfit::ClearData, BGSOutfit::~BGSOutfit: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

// OutfitArray, OutfitTLS, OutfitScope, ClearOutfitArray, ResetOutfitCount, ReleaseOutfitArray,
// data, capacity, pad0C, count, pad14, saved: GUESS(low); represented heap-array and TLS ownership.
void ClearOutfitArray(void*);
void ResetOutfitCount(std::uint32_t*);
void ReleaseOutfitArray(void*);
struct OutfitArray {
    ~OutfitArray() {
        if (data) { ClearOutfitArray(this); count = 0; }
        ResetOutfitCount(&count);
        ReleaseOutfitArray(this);
    }
    void* data;
    std::uint32_t capacity, pad0C, count, pad14;
};
static_assert(sizeof(OutfitArray)==0x18, "outfit array size");
class BGSOutfit : public TESForm
{
public:
    BGSOutfit();
    virtual void ClearData();  // compared: 0x264820
    OutfitArray items;
    virtual ~BGSOutfit();  // compared: 0x264d80 (scalar deleting destructor)
};
