// ActiveEffectReferenceEffectController functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s11-referenceeffectcontroll-activeef-419a131a48fa
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-upstream-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x5dc6d0, 10 bytes: ActiveEffectReferenceEffectController::GetElapsedTime
//   RVA 0x5dc7f0, 13 bytes: ActiveEffectReferenceEffectController::GetNoInitialFlare
//   RVA 0x5dc760, 15 bytes: ActiveEffectReferenceEffectController::GetSourcePosition
//   RVA 0x5dc810, 26 bytes: ActiveEffectReferenceEffectController::GetEffectPersists
//   RVA 0x5dc830, 26 bytes: ActiveEffectReferenceEffectController::GetGoryVisuals
//   RVA 0x5dc990, 56 bytes: ActiveEffectReferenceEffectController::GetHitEffectShader
//   RVA 0x5dc950, 57 bytes: ActiveEffectReferenceEffectController::GetHitEffectArt
//   RVA 0x5dc660, 61 bytes: ActiveEffectReferenceEffectController::SetTarget
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "ActiveEffectReferenceEffectController.h"

float ActiveEffectReferenceEffectController::GetElapsedTime()
{
    return owner->elapsed;
}

bool ActiveEffectReferenceEffectController::GetNoInitialFlare()
{
    return TestBit(owner->flags, 4);
}

const NiPoint3& ActiveEffectReferenceEffectController::GetSourcePosition()
{
    return owner->source->position;
}

bool ActiveEffectReferenceEffectController::GetEffectPersists()
{
    return TestBit(GetEffectRefData(owner)->flags, 12);
}

bool ActiveEffectReferenceEffectController::GetGoryVisuals()
{
    return TestBit(GetEffectRefData(owner)->flags, 14);
}

TESEffectShader* ActiveEffectReferenceEffectController::GetHitEffectShader()
{
    ActiveEffectOwner* a_owner = owner;
    const std::uint32_t flags = a_owner->flags;
    if (!TestBit(flags, 1)) {
        return GetEffectShaderForRef(GetEffectRefData(a_owner), TestBit(flags, 12));
    }
    return nullptr;
}

BGSArtObject* ActiveEffectReferenceEffectController::GetHitEffectArt()
{
    ActiveEffectOwner* a_owner = owner;
    const std::uint32_t flags = a_owner->flags;
    if (!TestBit(flags, 2)) {
        return GetEffectArtForRef(GetEffectRefData(a_owner), TestBit(flags, 12));
    }
    return nullptr;
}
