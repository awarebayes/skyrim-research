// TESWeightForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESWeightForm.h
// and the vftables of the pinned image. BaseFormComponent is a stand-in, labelled where
// it is declared; only class names, base
// chain, slot order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESWeightForm: EXE_RTTI; class name and base from the image RTTI
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


// TESWeightForm: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
class TESWeightForm : public BaseFormComponent
{
public:
	// TESWeightForm::~TESWeightForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 00
	~TESWeightForm() override;  // 00
	// TESWeightForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 01
	void InitializeDataComponent() override;  // 01
	// TESWeightForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 02
	void ClearDataComponent() override;  // 02
	// TESWeightForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 03
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03

	// weight: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	float weight;  // 08
	// pad0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad0C;  // 0C
};
static_assert(sizeof(TESWeightForm) == 0x10, "layout");
