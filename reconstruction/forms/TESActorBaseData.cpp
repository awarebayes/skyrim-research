// TESActorBaseData: virtual accessors, ClearDataComponent and InitializeDataComponent, build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s04-baseformcomponent-tesactorbasedata
// RVA 0x1de5e0, 3 bytes (Unk_07);
// RVA 0x1de5f0, 5 bytes (GetVoiceType);
// RVA 0x1de5c0, 7 bytes (GetInvulnerable);
// RVA 0x1de5d0, 9 bytes (GetIsGhost);
// RVA 0x1dc630, 38 bytes (ClearDataComponent);
// RVA 0x1dc5e0, 59 bytes (InitializeDataComponent);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "TESActorBaseData.h"

// gDefaultBaseDisposition: GUESS(low); a byte global at 0x20780f8 copied into baseDisposition
extern std::uint8_t gDefaultBaseDisposition;

namespace
{
    // TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
    inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
    {
        return ((a_flags >> a_bit) & 1) != 0;
    }
}

bool TESActorBaseData::GetIsGhost() const
{
    return TestBit(actorData.actorBaseFlags, 29);
}

bool TESActorBaseData::GetInvulnerable() const
{
    return TestBit(actorData.actorBaseFlags, 31);
}

bool TESActorBaseData::Unk_07()
{
    return true;
}

BGSVoiceType* TESActorBaseData::GetVoiceType()
{
    return voiceType;
}

void TESActorBaseData::ClearDataComponent()
{
    factions.Clear();
}

void TESActorBaseData::InitializeDataComponent()
{
    actorData.level = 1;
    actorData.calcLevelMin = 0;
    actorData.actorBaseFlags = 0;
    actorData.magickaOffset = 0;
    actorData.staminaOffset = 0;
    actorData.healthOffset = 0;
    actorData.calcLevelMax = 0;
    actorData.speedMult = 100;
    actorData.baseDisposition = gDefaultBaseDisposition;
    voiceType = nullptr;
    deathItem = nullptr;
    baseTemplateForm = nullptr;
    actorData.templateUseFlags = 0;
    actorData.bleedoutOverride = 0;
    unk38 = 0;
}
