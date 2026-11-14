// TESActionData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesactiondata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// TESActionData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// ActionInput, BGSActionData: STANDIN EXE_RTTI
// TESActionData::Unk_02: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// return type std::uint32_t of the slot: GUESS(low)
// ActionInput::~ActionInput, unknown08, unknown28: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class ActionInput
{
public:
    virtual ~ActionInput() = default;
    std::uint8_t unknown08[0x20];  // 08
};
static_assert(sizeof(ActionInput) == 0x28, "ActionInput size");

class BGSActionData : public ActionInput
{
public:
    std::uint8_t unknown28[0x38];  // 28
};
static_assert(sizeof(BGSActionData) == 0x60, "BGSActionData size");

class TESActionData : public BGSActionData
{
public:
    virtual std::uint32_t Unk_02();  // compared: 0x78db50
};
static_assert(sizeof(TESActionData) == 0x60, "TESActionData size");
