// MagicCaster member functions, build sse-steam-1-7-104.
// Labels: v2
//
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local listings of the pinned image
// with types from the header beside this file; labels revised by claude-opus-5-5 against the
// pinned community checkouts.
// Evidence: findings/third-batch-selection.md.
// Recipe: reconstruction/recipes/o2-fpfast.json; all four functions below are compared.
// The /fp:fast recipe is used because GetCurrentSpellCost and PlayReleaseSound compare floats for
// equality without the parity branch /fp:precise emits; the target has none (selection note "F").
//   MagicCaster::GetCurrentSpellCost  RVA 0x5c2cc0, 57 bytes
//   MagicCaster::InterruptCast        RVA 0x5caae0, 104 bytes
//   MagicCaster::FindPickTarget       RVA 0x5cef10, 163 bytes
//   MagicCaster::PlayReleaseSound     RVA 0x5cdf50, 165 bytes
// Names come from the header; the two unnamed callees (ContinueFindPickTarget, ApplySoundEvent)
// are guessed names (labelled in MagicCaster.h) bound by RVA hint. A byte match would not verify the names or the original source.
#include "MagicCaster.h"

float MagicCaster::GetCurrentSpellCost()
{
    MagicItem* spell = currentSpell;
    if (currentSpellCost == 1.0f && spell) {
        return spell->CalculateCost(GetCasterAsActor());
    }
    return currentSpellCost;
}

void MagicCaster::InterruptCast(bool a_refund)
{
    if (currentSpell) {
        InterruptCastImpl(a_refund);
        sounds[static_cast<std::uint32_t>(MagicSystem::SoundID::kCharge)].Stop();
        sounds[static_cast<std::uint32_t>(MagicSystem::SoundID::kReadyLoop)].Stop();
        sounds[static_cast<std::uint32_t>(MagicSystem::SoundID::kCastLoop)].Stop();
        state = State::kUnk09;
        SpellCast(false, 0, nullptr);
        FinishCast();
    }
}

MagicTarget* MagicCaster::FindPickTarget(NiPoint3& a_targetLocation, TESObjectCELL** a_targetCell, bhkPickData& a_pickData)
{
    MagicItem* spell = currentSpell;
    if (spell) {
        float range = spell->GetRange();
        if (Actor* caster = GetCasterAsActor()) {
            BGSEntryPoint::HandleEntryPoint(BGSEntryPoint::ENTRY_POINTS::kModSpellRange_TargetLoc, caster, spell, &range);
        }
        return ContinueFindPickTarget(spell->GetDelivery() == MagicSystem::Delivery::kTargetActor, range, a_targetLocation, a_targetCell, a_pickData);
    }
    return ContinueFindPickTarget(false, 0.0f, a_targetLocation, a_targetCell, a_pickData);
}

void MagicCaster::PlayReleaseSound(MagicItem* a_item)
{
    Actor* caster = GetCasterAsActor();
    if (a_item && caster && caster->currentProcess) {
        float soundEventMult = 1.0f;
        BGSEntryPoint::HandleEntryPoint(BGSEntryPoint::ENTRY_POINTS::kModSpellCastingSoundEvent, caster, a_item, &soundEventMult);
        if (soundEventMult != 0.0f) {
            if (EffectSetting* effect = a_item->GetAVEffect()) {
                std::int32_t level = AIFormulas::GetSoundLevelValue(effect->data.castingSoundLevel);
                caster->currentProcess->SetActorsDetectionEvent(caster, caster->data.location, level, caster);
                ApplySoundEvent(caster, level);
            }
        }
    }
}
