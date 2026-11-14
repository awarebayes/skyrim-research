// AlchemyItem declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-alchemyitem
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// AlchemyItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BaseFormComponent, TESForm, TESObject, TESBoundObject, MagicItem: STANDIN EXE_RTTI
// AlchemyItem::GetDelivery, AlchemyItem::GetCastingType, AlchemyItem::GetDataSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MagicSystem::Delivery, MagicSystem::CastingType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BaseFormComponent::~BaseFormComponent, unknown08, unknown20, unknown30, unknown90: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

namespace MagicSystem { enum class CastingType : int; }

namespace MagicSystem { enum class Delivery : int; }

class BaseFormComponent
{
public:
    virtual ~BaseFormComponent() = default;
};
static_assert(sizeof(BaseFormComponent) == 0x8, "BaseFormComponent size");

class TESForm : public BaseFormComponent
{
public:
};

class TESObject : public TESForm
{
public:
    std::uint8_t unknown08[0x18];  // 08
};
static_assert(sizeof(TESObject) == 0x20, "TESObject size");

class TESBoundObject : public TESObject
{
public:
    std::uint8_t unknown20[0x10];  // 20
};
static_assert(sizeof(TESBoundObject) == 0x30, "TESBoundObject size");

class MagicItem : public TESBoundObject
{
public:
    std::uint8_t unknown30[0x60];  // 30
};
static_assert(sizeof(MagicItem) == 0x90, "MagicItem size");

class AlchemyItem : public MagicItem
{
public:
    virtual MagicSystem::Delivery GetDelivery() const;  // compared: 0x1466e0
    virtual MagicSystem::CastingType GetCastingType() const;  // compared: 0x146670
    virtual std::uint32_t GetDataSize() const;  // compared: 0x1466d0

    std::uint8_t unknown90[0xD8];  // 90
};
static_assert(sizeof(AlchemyItem) == 0x168, "AlchemyItem size");
