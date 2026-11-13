// TESActorBase functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tesactorbase
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-2 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3b03a0, 11 bytes: TESActorBase::GetIsPlayerOwner
//   RVA 0x3afed0, 22 bytes: TESActorBase::IsAutoCalc
//   RVA 0x3afef0, 28 bytes: TESActorBase::SetAutoCalc
//   RVA 0x3cbc60, 52 bytes: TESActorBase::~TESActorBase
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESActorBase.h"

// TestBit: GUESS(low)
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESActorBase::TESActorBase()
{
}

// TODO body: RVA 0x3b03a0, 11 bytes, TESActorBase::GetIsPlayerOwner.
bool TESActorBase::GetIsPlayerOwner() const
{
    return *reinterpret_cast<const std::int32_t*>(reinterpret_cast<const char*>(this) - 0xd4) == 7;
}

// TODO body: RVA 0x3afed0, 22 bytes, TESActorBase::IsAutoCalc.
bool TESActorBase::IsAutoCalc() const
{
    if (*reinterpret_cast<const std::uint8_t*>(reinterpret_cast<const char*>(this) + 0x1a) == '+' &&
        TestBit(*reinterpret_cast<const std::uint32_t*>(reinterpret_cast<const char*>(this) + 0x38), 4)) {
        return true;
    }
    return false;
}

// TODO body: RVA 0x3afef0, 28 bytes, TESActorBase::SetAutoCalc.
void TESActorBase::SetAutoCalc(bool a_autoCalc)
{
    if (*reinterpret_cast<const std::uint8_t*>(reinterpret_cast<const char*>(this) + 0x1a) == '+') {
        reinterpret_cast<TESActorBaseData*>(reinterpret_cast<char*>(this) + 0x30)->SetFlagBit(0x10, a_autoCalc, true);
    }
}

// TODO body: RVA 0x3cbc60, 52 bytes, TESActorBase::~TESActorBase; compared as the scalar deleting
// destructor. If the target calls a separate destructor, keep only the declaration and delete this
// definition (cookbook rule 18).
