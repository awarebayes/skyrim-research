// BGSActionData declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bgsactiondata
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSActionData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// ActionInput: STANDIN EXE_RTTI
// BGSActionData::Process: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
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
    virtual bool Process();  // compared: 0x240f40

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown28[0x38];  // 28
};
static_assert(sizeof(BGSActionData) == 0x60, "BGSActionData size");
