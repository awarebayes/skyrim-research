// TESEnchantableForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESEnchantableForm.h
// and the vftables of the pinned image. BaseFormComponent and EnchantmentItem are stand-ins, labelled where
// they are declared; only class names, base
// chain, slot order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESEnchantableForm: EXE_RTTI; class name and base from the image RTTI
#pragma once

#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0; defined inline, the target's deleting destructors store its vptr themselves
	virtual ~BaseFormComponent() {}  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	virtual void CopyComponent(BaseFormComponent* a_rhs);  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");


class EnchantmentItem;

// TESEnchantableForm: EXE_RTTI; class name and base from the image RTTI, 5 primary vftable slots
class TESEnchantableForm : public BaseFormComponent
{
public:
	// TESEnchantableForm::TESEnchantableForm: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); defined so the unit emits the vftable
	TESEnchantableForm();
	// TESEnchantableForm::~TESEnchantableForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 00
	~TESEnchantableForm() override;  // 00
	// TESEnchantableForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 01
	void InitializeDataComponent() override;  // 01
	// TESEnchantableForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 02
	void ClearDataComponent() override;  // 02
	// TESEnchantableForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 03
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03
	// TESEnchantableForm::GetCastingType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 04
	virtual std::uint16_t GetCastingType() const;  // 04

	// formEnchanting: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	EnchantmentItem* formEnchanting;  // 08
	// castingType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares stl::enumeration<MagicSystem::CastingType, std::uint16_t>, a plain word here
	std::uint16_t castingType;  // 10
	// amountofEnchantment: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint16_t amountofEnchantment;  // 12
	// pad14: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad14;  // 14
};
static_assert(sizeof(TESEnchantableForm) == 0x18, "layout");
