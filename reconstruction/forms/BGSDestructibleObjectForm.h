// BGSDestructibleObjectForm type declarations, build sse-steam-1-7-104.
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

// DestructibleObjectData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only a destroy helper is called
struct DestructibleObjectData
{
	// Destroy: GUESS(low); the target calls one helper with the data and 1, target 0x1d6850
	void Destroy(std::uint32_t a_flags);

	// unk00: GUESS(low); members not modelled
	std::uint8_t unk00[0x20];  // 00
};
static_assert(sizeof(DestructibleObjectData) == 0x20, "layout");

// BGSDestructibleObjectForm: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BGSDestructibleObjectForm 0x10: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BGSDestructibleObjectForm : public ::BaseFormComponent
{
public:
	// BGSDestructibleObjectForm::~BGSDestructibleObjectForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1d67f0, inherited name
	~BGSDestructibleObjectForm() override;  // 00
	// BGSDestructibleObjectForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1d2750, inherited name
	void InitializeDataComponent() override;  // 01
	// BGSDestructibleObjectForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1d2760, inherited name
	void ClearDataComponent() override;  // 02
	// BGSDestructibleObjectForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1d2af0, inherited name
	void CopyComponent() override;  // 03

		// data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	DestructibleObjectData* data;  // 08
};
static_assert(sizeof(BGSDestructibleObjectForm) == 0x10, "layout");
