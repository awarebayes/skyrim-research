// TESLeveledList type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESLeveledList.h
// and the vftables of the pinned image. BaseFormComponent, TESGlobal and the entry type are stand-ins, labelled where
// they are declared; only class names, base
// chain, slot order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESLeveledList: EXE_RTTI; class name and base from the image RTTI
#pragma once

#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	virtual ~BaseFormComponent();  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	virtual void CopyComponent(BaseFormComponent* a_rhs);  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");


class LEVELED_OBJECT;

// TESGlobal: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the float value is declared, at the offset the listing reads
class TESGlobal
{
public:
	// unk00: GUESS(low); TESForm, TESFullName and the type character precede value
	std::uint8_t unk00[0x34];  // 00
	// value: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	float value;  // 34
};

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
	return ((a_flags >> a_bit) & 1) != 0;
}

// TESLeveledList: EXE_RTTI; class name and base from the image RTTI, 8 primary vftable slots
class TESLeveledList : public BaseFormComponent
{
public:
	// TESLeveledList::~TESLeveledList: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 00
	~TESLeveledList() override;  // 00
	// TESLeveledList::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 01
	void InitializeDataComponent() override;  // 01
	// TESLeveledList::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 02
	void ClearDataComponent() override;  // 02
	// TESLeveledList::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 03
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03
	// TESLeveledList::GetChanceNone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 04
	virtual std::uint8_t GetChanceNone();  // 04
	// TESLeveledList::GetMultCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 05
	virtual bool GetMultCalc();  // 05
	// TESLeveledList::GetLevDifferenceMax: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 06
	virtual std::int32_t GetLevDifferenceMax();  // 06
	// TESLeveledList::GetCanContainFormsOfType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 07
	virtual bool GetCanContainFormsOfType(std::uint8_t a_type) const = 0;  // 07
	// GetUseAll: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); a non-virtual helper reading the kUseAll bit
	bool GetUseAll();

	// entries: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares SimpleArray<LEVELED_OBJECT>, a pointer here
	LEVELED_OBJECT* entries;  // 08
	// chanceNone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::int8_t chanceNone;  // 10
	// llFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares the Flag enum, a byte here
	std::uint8_t llFlags;  // 11
	// numEntries: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint8_t numEntries;  // 12
	// unk13: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint8_t unk13;  // 13
	// pad14: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad14;  // 14
	// unk18: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	void* unk18;  // 18
	// chanceGlobal: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESGlobal* chanceGlobal;  // 20
};
static_assert(sizeof(TESLeveledList) == 0x28, "layout");
