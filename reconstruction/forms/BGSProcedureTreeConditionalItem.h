// BGSProcedureTreeConditionalItem declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-a-bgsproceduretreeconditionalitem
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BGSProcedureTreeConditionalItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// IProcedureTreeItem: STANDIN EXE_RTTI
// BGSProcedureTreeConditionalItem::Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSProcedureTreeConditionalItem::Unk_01: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; the listing takes a second argument and passes a third through unchanged to TESCondition::Copy
// BGSProcedureTreeConditionalItem::Unk_10: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares void Unk_10(void), the listing takes the other item and returns a bool comparing the qwords its two virtual slots return
// IProcedureTreeItem::Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IProcedureTreeItem::Unk_05, IProcedureTreeItem::Unk_06: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares void, the listing dereferences the returned pointer
// IProcedureTreeItem::~IProcedureTreeItem, IProcedureTreeItem::Unk_01, IProcedureTreeItem::Unk_02, IProcedureTreeItem::Unk_04: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::SeekNextSubrecord: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESCondition: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// TESCondition::Copy: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// TESCondition::Load, unknown00: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class TESForm;
class IProcedureTreeItem;

class TESFile
{
public:
    bool SeekNextSubrecord();
};

class TESCondition
{
public:
    void Copy(const TESCondition* a_other, TESForm* a_arg2);
    void Load(TESFile* a_mod);

    std::uint8_t unknown00[0x8];  // 00
};
static_assert(sizeof(TESCondition) == 0x8, "TESCondition size");

class IProcedureTreeItem
{
public:
    virtual ~IProcedureTreeItem() = default;
    virtual void Unk_01();  // 01
    virtual void Unk_02();  // 02
    virtual void Load(TESFile* a_mod);  // 03
    virtual void Unk_04();  // 04
    virtual std::int64_t* Unk_05();  // 05
    virtual std::int64_t* Unk_06();  // 06
};
static_assert(sizeof(IProcedureTreeItem) == 0x8, "IProcedureTreeItem size");

class BGSProcedureTreeConditionalItem : public IProcedureTreeItem
{
public:
    virtual void Unk_01(const BGSProcedureTreeConditionalItem* a_other, TESForm* a_arg2);  // compared: 0x48a310
    virtual void Load(TESFile* a_mod);  // compared: 0x48a340
    virtual bool Unk_10(IProcedureTreeItem* a_other);  // compared: 0x48a3b0

    // members
    TESCondition condition;  // 08
};
static_assert(sizeof(BGSProcedureTreeConditionalItem) == 0x10, "BGSProcedureTreeConditionalItem size");
