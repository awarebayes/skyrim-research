// TESProduceForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESProduceForm.h
// and the vftables of the pinned image. BaseFormComponent and the pointer types are stand-ins, labelled where
// they are declared; only class names, base
// chain, slot order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESProduceForm: EXE_RTTI; class name and base from the image RTTI
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


class BGSSoundDescriptorForm;
class TESBoundObject;

// TESProduceForm: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
class TESProduceForm : public BaseFormComponent
{
public:
	// TESProduceForm::TESProduceForm: GUESS(low); defined so the unit emits the vftable
	TESProduceForm();
	// TESProduceForm::~TESProduceForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 00
	~TESProduceForm() override;  // 00
	// TESProduceForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 01
	void InitializeDataComponent() override;  // 01
	// TESProduceForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 02
	void ClearDataComponent() override;  // 02
	// TESProduceForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 03
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03

	// harvestSound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSSoundDescriptorForm* harvestSound;  // 08
	// produceItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESBoundObject* produceItem;  // 10
	// produceChance: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG sizes it by SEASON::kTotal, four bytes here
	std::int8_t produceChance[4];  // 18
	// pad1C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad1C;  // 1C
};
static_assert(sizeof(TESProduceForm) == 0x20, "layout");
