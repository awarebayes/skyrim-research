// TESAIForm type declarations, build sse-steam-1-7-104.
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

// AIDATA_GAME: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bit-field names and order from the community header, declared
// with a 32-bit storage unit because the target updates the first word as a whole
struct AIDATA_GAME
{
	// aggression1..aggroRadiusBehaviour, pad2_5..pad2_7, pad3, aggroRadius, noSlowApproach, padA_1..padA_7, padB: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t aggression1: 1;
	std::uint32_t aggression2: 1;
	std::uint32_t confidence1: 1;
	std::uint32_t confidence2: 1;
	std::uint32_t confidence3: 1;
	std::uint32_t energyLevel1: 1;
	std::uint32_t energyLevel2: 1;
	std::uint32_t energyLevel3: 1;
	std::uint32_t energyLevel4: 1;
	std::uint32_t energyLevel5: 1;
	std::uint32_t energyLevel6: 1;
	std::uint32_t energyLevel7: 1;
	std::uint32_t energyLevel8: 1;
	std::uint32_t morality1: 1;
	std::uint32_t morality2: 1;
	std::uint32_t mood1: 1;
	std::uint32_t mood2: 1;
	std::uint32_t mood3: 1;
	std::uint32_t assistance1: 1;
	std::uint32_t assistance2: 1;
	std::uint32_t aggroRadiusBehaviour: 1;
	std::uint32_t pad2_5: 1;
	std::uint32_t pad2_6: 1;
	std::uint32_t pad2_7: 1;
	std::uint32_t pad3: 8;
	std::uint16_t aggroRadius[3];
	bool noSlowApproach: 1;
	bool padA_1: 1;
	bool padA_2: 1;
	bool padA_3: 1;
	bool padA_4: 1;
	bool padA_5: 1;
	bool padA_6: 1;
	bool padA_7: 1;
	std::uint8_t padB;
};
static_assert(sizeof(AIDATA_GAME) == 0xC, "layout");

// PackageList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the BSSimpleList of packages is modelled as two pointers
struct PackageList
{
	// Clear: GUESS(low); helper ClearDataComponent tail-calls on the list, target 0x4a2c50
	void Clear();

	// unk00: GUESS(low); BSSimpleList<TESPackage*> in the community header, not modelled
	void* unk00[2];  // 00
};
static_assert(sizeof(PackageList) == 0x10, "layout");

// TESAIForm: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof TESAIForm 0x28: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESAIForm : public ::BaseFormComponent
{
public:
	// TESAIForm::~TESAIForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1df010, inherited name
	~TESAIForm() override;  // 00
	// TESAIForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1de800, inherited name
	void InitializeDataComponent() override;  // 01
	// TESAIForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1de820, inherited name
	void ClearDataComponent() override;  // 02
	// TESAIForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1de830, inherited name
	void CopyComponent() override;  // 03

	// aiData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	AIDATA_GAME aiData;  // 08
	// aiPackages: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	PackageList aiPackages;  // 18
};
static_assert(sizeof(TESAIForm) == 0x28, "layout");
