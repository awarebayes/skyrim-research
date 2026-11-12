// BGSOverridePackCollection type declarations, build sse-steam-1-7-104.
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

// BGSListForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
class BGSListForm;

// BGSOverridePackCollection: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BGSOverridePackCollection 0x28: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BGSOverridePackCollection : public ::BaseFormComponent
{
public:
	// BGSOverridePackCollection::~BGSOverridePackCollection: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1db070, inherited name
	// BGSOverridePackCollection::BGSOverridePackCollection: GUESS(low); defined so the unit emits the vftable and with it the deleting destructor
	BGSOverridePackCollection();
	~BGSOverridePackCollection() override;  // 00
	// BGSOverridePackCollection::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1daad0, inherited name
	void InitializeDataComponent() override;  // 01
	// BGSOverridePackCollection::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1daaf0, inherited name
	void ClearDataComponent() override;  // 02
	// BGSOverridePackCollection::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1dab00, inherited name
	void CopyComponent() override;  // 03

		// spectatorOverRidePackList: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSListForm* spectatorOverRidePackList;  // 08
	// observeCorpseOverRidePackList: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSListForm* observeCorpseOverRidePackList;  // 10
	// guardWarnOverRidePackList: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSListForm* guardWarnOverRidePackList;  // 18
	// enterCombatOverRidePackList: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSListForm* enterCombatOverRidePackList;  // 20
};
static_assert(sizeof(BGSOverridePackCollection) == 0x28, "layout");
