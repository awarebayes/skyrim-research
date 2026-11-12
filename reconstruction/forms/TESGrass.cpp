// TESGrass accessors and destructor, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x2709b0, 4 bytes (GetUnderwaterState); RVA 0x270a30, 4 bytes (SetUnderwaterState);
// RVA 0x270900, 5 bytes (GetDensity); RVA 0x270910, 5 bytes (GetDistanceFromWaterLevel);
// RVA 0x270960, 5 bytes (GetMaxSlopeDegrees); RVA 0x270990, 5 bytes (GetMinSlopeDegrees);
// RVA 0x270890, 84 bytes (~TESGrass, the deleting destructor).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT); the powerof3 fork (GPL-3.0) uses the same ones.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// TESModel::~TESModel and TESBoundObject::~TESBoundObject are called by the compiler-generated
// base destruction; they are declared, not defined, in this unit.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The seven functions above are compared.
#include "TESGrass.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the deleting destructor, as the original unit did. Its body is a minimal stand-in.
TESGrass::TESGrass()
{
}

TESGrass::~TESGrass()
{
}

std::uint8_t TESGrass::GetDensity() const
{
    return data.density;
}

std::uint8_t TESGrass::GetMinSlopeDegrees() const
{
    return data.minSlopeDegrees;
}

std::uint8_t TESGrass::GetMaxSlopeDegrees() const
{
    return data.maxSlopeDegrees;
}

std::uint16_t TESGrass::GetDistanceFromWaterLevel() const
{
    return data.distanceFromWaterLevel;
}

TESGrass::GRASS_WATER_STATE TESGrass::GetUnderwaterState() const
{
    return data.underwater;
}

void TESGrass::SetUnderwaterState(GRASS_WATER_STATE a_waterState)
{
    data.underwater = a_waterState;
}
