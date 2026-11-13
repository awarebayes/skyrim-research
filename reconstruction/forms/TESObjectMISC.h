// TESObjectMISC declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s03-tesboundobject-tesobjectmisc
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// TESObjectMISC: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// TESObject, TESBoundObject: STANDIN EXE_RTTI
// TESObjectMISC::SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// MiscSaveBlock, MiscSaveBlock::SaveData: GUESS(low)
// unknownBase, saveBlock88: GUESS(low)
#pragma once

#include <cstdint>
#include "../forms/TESForm.h"

class TESObject : public TESForm
{
public:
};

class TESBoundObject : public TESObject
{
public:
};

class MiscSaveBlock
{
public:
    void SaveData(BGSSaveFormBuffer* a_buf);
};

class TESObjectMISC : public TESBoundObject
{
public:
    virtual void SaveGame(BGSSaveFormBuffer* a_buf);  // compared: 0x286eb0

    std::uint8_t unknownBase[0x88 - sizeof(TESBoundObject)];
    MiscSaveBlock saveBlock88;  // 88
};
