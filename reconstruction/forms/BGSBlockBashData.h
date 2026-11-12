// BGSBlockBashData type declarations, build sse-steam-1-7-104.
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

// BGSImpactDataSet, BGSMaterialType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
class BGSImpactDataSet;
class BGSMaterialType;

// BGSBlockBashData: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BGSBlockBashData 0x18: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BGSBlockBashData : public ::BaseFormComponent
{
public:
	// BGSBlockBashData::~BGSBlockBashData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1d23c0, inherited name
	~BGSBlockBashData() override;  // 00
	// BGSBlockBashData::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1d2240, inherited name
	void InitializeDataComponent() override;  // 01
	// BGSBlockBashData::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1d2260, inherited name
	void ClearDataComponent() override;  // 02
	// BGSBlockBashData::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1d2340, inherited name
	void CopyComponent() override;  // 03

	// blockBashImpactDataSet: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSImpactDataSet* blockBashImpactDataSet;  // 08
	// altBlockMaterialType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSMaterialType* altBlockMaterialType;  // 10
};
static_assert(sizeof(BGSBlockBashData) == 0x18, "layout");
