// TESContainer type declarations, build sse-steam-1-7-104.
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

// TESBoundObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only compared by pointer
class TESBoundObject;

// ContainerObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only count and obj are read
struct ContainerObject
{
	// count: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::int32_t count;  // 00
	// pad04: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad04;  // 04
	// obj: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESBoundObject* obj;  // 08
	// itemExtra: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque pointer
	void* itemExtra;  // 10
};
static_assert(sizeof(ContainerObject) == 0x18, "layout");

// TESContainer: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof TESContainer 0x18: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESContainer : public ::BaseFormComponent
{
public:
	// TESContainer::~TESContainer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1e1160, inherited name
	~TESContainer() override;  // 00
	// TESContainer::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1e0040, inherited name
	void InitializeDataComponent() override;  // 01
	// TESContainer::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1e0050, inherited name
	void ClearDataComponent() override;  // 02
	// TESContainer::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1e0060, inherited name
	void CopyComponent() override;  // 03

	// GetItemCount: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); signature derived from the listing
	std::int32_t GetItemCount(TESBoundObject* a_object) const;

	// containerObjects: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	ContainerObject** containerObjects;  // 08
	// numContainerObjects: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t numContainerObjects;  // 10
	// allowStolenItems: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	bool allowStolenItems;  // 14
	// unk15: GUESS(low); tail padding
	std::uint8_t unk15[3];  // 15
};
static_assert(sizeof(TESContainer) == 0x18, "layout");
