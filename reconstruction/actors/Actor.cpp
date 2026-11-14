// Actor member functions, build sse-steam-1-7-104.
//
// Labels: v2
// Compared: HasOutfitItems, GetLevel, IsAttacking, HasShout, GetMoveDirectionRelativeToFacing,
// GetVoiceRecoveryTime, IsInRagdollState, GetActorValueModifier.
// RVA 0x2e7fc0, 156 bytes (HasOutfitItems). RVA 0x6797a0, 13 bytes (GetLevel).
// RVA 0x6cb920, 14 bytes (IsAttacking). RVA 0x6d7750, 16 bytes (HasShout).
// RVA 0x6af1b0, 20 bytes (GetMoveDirectionRelativeToFacing). RVA 0x6d92b0, 20 bytes (GetVoiceRecoveryTime).
// RVA 0x687c20, 102 bytes (IsInRagdollState). RVA 0x6c5440, 115 bytes (GetActorValueModifier).
// Evidence: findings/second-batch-selection.md (0x2e7fc0), findings/third-batch-selection.md (the others).
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local listing of the pinned image
// with types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// The HasOutfitItems callee at RVA 0x1648b0 is declared as FindOutfitExtra (label below).
// FindOutfitExtra: GUESS; callee of HasOutfitItems at RVA 0x1648b0.
// A byte match shows this source and recipe produce the checked code; it does not verify
// the community name or that the original source looked like this.
#include "Actor.h"

std::uint16_t Actor::GetLevel() const
{
    return static_cast<TESNPC*>(data.objectReference)->GetLevel();
}

bool Actor::IsAttacking() const
{
    return GetAttackState() != ATTACK_STATE_ENUM::kNone;
}

bool Actor::HasShout(TESShout* a_shout) const
{
    return static_cast<TESNPC*>(data.objectReference)->HasShout(a_shout);
}

float Actor::GetMoveDirectionRelativeToFacing()
{
    return currentProcess ? currentProcess->GetMoveDirectionRelativeToFacing() : 0.0f;
}

float Actor::GetVoiceRecoveryTime()
{
    return currentProcess ? currentProcess->GetVoiceRecoveryTime() : 0.0f;
}

void Actor::SetAvoidanceDisabled(bool)
{
}

void Actor::UseSkill(ActorValue, float, TESForm*)
{
}

void Actor::AddPerk(BGSPerk*, std::uint32_t)
{
}

bool Actor::IsInRagdollState() const
{
    if (IsParalyzed()) {
        return true;
    }
    if (IsDead() && !IsReanimating()) {
        return true;
    }
    const auto knock = GetKnockState();
    if (knock != KNOCK_STATE_ENUM::kNormal && knock != KNOCK_STATE_ENUM::kGetUp) {
        return true;
    }
    if (IsUnconscious()) {
        return true;
    }
    return false;
}

float Actor::GetActorValueModifier(ACTOR_VALUE_MODIFIER a_modifier, ActorValue a_value) const
{
    const Modifiers* mods;
    switch (a_value) {
    case ActorValue::kHealth:
        mods = &healthModifiers;
        break;
    case ActorValue::kMagicka:
        mods = &magickaModifiers;
        break;
    case ActorValue::kStamina:
        mods = &staminaModifiers;
        break;
    case ActorValue::kVoicePoints:
        mods = &voicePointsModifiers;
        break;
    default:
        mods = avStorage.GetModifiers(a_value);
        break;
    }
    return mods ? mods->modifiers[static_cast<int>(a_modifier)] : 0.0f;
}

bool Actor::HasOutfitItems(BGSOutfit* a_outfit)
{
    if (a_outfit) {
        InventoryChanges* changes = MakeInventoryChanges();
        std::uint32_t     id      = a_outfit->formID;
        for (auto* entries = changes->entryList; entries && entries->item; entries = entries->next) {
            for (auto* lists = entries->item->extraLists; lists && (lists->next || lists->item);
                 lists       = lists->next) {
                OutfitExtra* extra = FindOutfitExtra(lists->item);
                if (extra && (id == 0 || extra->outfitID == id)) {
                    return true;
                }
            }
        }
    }
    return false;
}
