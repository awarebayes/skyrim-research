// BGSEquipType type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): the class header and
// the vftables of the pinned image. Slot signatures other than the compared ones are placeholders.
// BaseFormComponent: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only class names, base chain,
// slot order and sizes are claimed.
#pragma once

#include <cstddef>
#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x146610
	virtual ~BaseFormComponent() {}  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x15a97c8
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x15a97c8
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x145470
	virtual void CopyComponent();  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");

// BGSEquipSlot: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
class BGSEquipSlot;

// BGSEquipType: EXE_RTTI; class name and base from the image RTTI, 6 primary vftable slots
// sizeof BGSEquipType 0x10: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BGSEquipType : public ::BaseFormComponent
{
public:
	// BGSEquipType::~BGSEquipType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1d75c0, inherited name
	~BGSEquipType() override;  // 00
	// BGSEquipType::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1d7220, inherited name
	void InitializeDataComponent() override;  // 01
	// BGSEquipType::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1d7230, inherited name
	void ClearDataComponent() override;  // 02
	// BGSEquipType::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1d72b0, inherited name
	void CopyComponent() override;  // 03
	// BGSEquipType::GetEquipSlot: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x146700
	virtual BGSEquipSlot* GetEquipSlot() const;  // 04
	// BGSEquipType::SetEquipSlot: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5, target 0x146a50
	virtual void SetEquipSlot(BGSEquipSlot* a_slot);  // 05

	// equipSlot: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSEquipSlot* equipSlot;  // 08
};
static_assert(sizeof(BGSEquipType) == 0x10, "layout");
