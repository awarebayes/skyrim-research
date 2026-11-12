// TESAttackDamageForm type declarations, build sse-steam-1-7-104.
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

// TESAttackDamageForm: EXE_RTTI; class name and base from the image RTTI, 5 primary vftable slots
// sizeof TESAttackDamageForm 0x10: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESAttackDamageForm : public ::BaseFormComponent
{
public:
	// TESAttackDamageForm::~TESAttackDamageForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1df1a0, inherited name
	// TESAttackDamageForm::TESAttackDamageForm: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); defined so the unit emits the vftable and with it the deleting destructor
	TESAttackDamageForm();
	~TESAttackDamageForm() override;  // 00
	// TESAttackDamageForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1df0c0, inherited name
	void InitializeDataComponent() override;  // 01
	// TESAttackDamageForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1df0d0, inherited name
	void ClearDataComponent() override;  // 02
	// TESAttackDamageForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1df0e0, inherited name
	void CopyComponent() override;  // 03
	// TESAttackDamageForm::GetAttackDamage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x1df130
	virtual std::uint16_t GetAttackDamage() const;  // 04

		// attackDamage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint16_t attackDamage;  // 08
	// unk0A: GUESS(low); pad0A and pad0C in the community header
	std::uint8_t unk0A[6];  // 0A
};
static_assert(sizeof(TESAttackDamageForm) == 0x10, "layout");
