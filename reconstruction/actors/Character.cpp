// Character member functions, build sse-steam-1-7-104.
//
// Labels: v2
// Licence: uses some member names from powerof3/CommonLibSSE (see the header), so this file is GPL-3.0.
// Compared: GetRotationX, Unk_C4, GetBiped2, StartDeferredKill, Revert, ~Character (scalar deleting
// destructor), SetCrimeFaction.
// RVA 0x692ea0, 6 bytes (GetRotationX). RVA 0x73ad70, 7 bytes (Unk_C4). RVA 0x73a760, 8 bytes (GetBiped2).
// RVA 0x6cc910, 17 bytes (StartDeferredKill). RVA 0x73a8b0, 49 bytes (Revert).
// RVA 0x73abc0, 52 bytes (~Character, the scalar deleting destructor). RVA 0x67eab0, 234 bytes (SetCrimeFaction).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local listings of the pinned image with
// types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Callees without a community name carry made-up names, labelled in the header, and are bound by RVA in the unit's
// bind hints; Character::~Character (plain) and Actor::Revert are called, not defined here.
// A byte match shows this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "Character.h"

// The constructor is not compared: it is defined so that this unit emits the vftable and with
// it the deleting destructor, as the original unit did. ~Character itself is declared, not defined:
// the deleting destructor calls it out of line (the plain destructor lives in another unit).
Character::Character()
{
}

float Character::GetRotationX() const
{
    return unk48;
}

void Character::Unk_C4(std::uint8_t a_arg1)
{
    unk27A = a_arg1;
}

const BSTSmartPointer<BipedAnim>& Character::GetBiped2() const
{
    return biped2;
}

void Character::StartDeferredKill()
{
    if (currentProcess) {
        currentProcess->StartDeferredKill();
    }
}

void Character::Revert(BGSLoadFormBuffer* a_buf)
{
    Actor::Revert(a_buf);
    OnArmorActorValueChanged();
    unkE8 &= ~0x40000000u;
    unk279 = 0;
}

// TestBit: GUESS(low); a flag-word bit test by bit index, probably an engine flag accessor that takes the
// bit number. The word is passed by value so that the test is a shift and a mask of the loaded word.
static bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

void Character::SetCrimeFaction(TESFaction* a_faction)
{
    if (a_faction) {
        if (!TestBit(a_faction->factionFlags, 6)) {
            return;
        }
        if (!IsInFaction(a_faction)) {
            if (TestBit(unk40->actorData.actorBaseFlags, 5)) {
                unk40->actorData.AddFaction(a_faction, 1);
            } else {
                AddChange(0x80000000u);
                ExtraFactionChanges* changes = extraList.GetFactionChanges();
                if (!changes) {
                    extraList.AddFactionChanges();
                    changes = extraList.GetFactionChanges();
                }
                if (changes) {
                    changes->SetFactionRank(a_faction, 1);
                }
            }
            UpdateFactionsA(true);
            UpdateFactionsB();
            if (currentProcess && currentProcess->cachedValues) {
                currentProcess->cachedValues->flags &= ~CachedValues::kOwnerIsInCombatantFaction;
            }
        }
    }
    extraList.RemoveFactionChange(a_faction);
}
