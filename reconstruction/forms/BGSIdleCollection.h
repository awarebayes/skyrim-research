// BGSIdleCollection type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): the class header and
// the vftables of the pinned image. Slot signatures other than the compared ones are placeholders.
// BaseFormComponent: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only class names, base chain,
// slot order and sizes are claimed.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/fallout_shared/bgsidlecollection.cpp:159
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

// TESIdleForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
class TESIdleForm;

// BGSIdleCollection: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BGSIdleCollection 0x20: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BGSIdleCollection : public ::BaseFormComponent
{
public:
	// BGSIdleCollection::~BGSIdleCollection: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1d84c0, inherited name
	// BGSIdleCollection::Ctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the community name for the constructor
	BGSIdleCollection();
	~BGSIdleCollection() override;  // 00
	// BGSIdleCollection::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1d76e0, inherited name
	void InitializeDataComponent() override;  // 01
	// BGSIdleCollection::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1d7700, inherited name
	void ClearDataComponent() override;  // 02
	// BGSIdleCollection::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1d77a0, inherited name
	void CopyComponent() override;  // 03

		// idleFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG wraps it in stl::enumeration<IdleFlags, std::int8_t>
	std::int8_t idleFlags;  // 08
	// idleCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::int8_t idleCount;  // 09
	// unk0A: GUESS(low); pad0A and pad0C in the community header
	std::uint8_t unk0A[6];  // 0A
	// idles: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESIdleForm** idles;  // 10
	// timerCheckForIdle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	float timerCheckForIdle;  // 18
	// unk1C: GUESS(low); pad1C in the community header
	std::uint32_t unk1C;  // 1C
};
static_assert(sizeof(BGSIdleCollection) == 0x20, "layout");
