// TESActorBaseData type declarations, build sse-steam-1-7-104.
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

// BGSVoiceType, TESLevItem: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
class BGSVoiceType;
class TESLevItem;

// ACTOR_BASE_DATA: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); fields and offsets from the community header, flags kept as a plain word
struct ACTOR_BASE_DATA
{
	std::uint32_t actorBaseFlags;  // 00
	std::int16_t magickaOffset;  // 04
	std::int16_t staminaOffset;  // 06
	std::uint16_t level;  // 08
	std::uint16_t calcLevelMin;  // 0A
	std::uint16_t calcLevelMax;  // 0C
	std::uint16_t speedMult;  // 0E
	std::uint16_t baseDisposition;  // 10
	std::uint16_t templateUseFlags;  // 12
	std::int16_t healthOffset;  // 14
	std::int16_t bleedoutOverride;  // 16
};
static_assert(sizeof(ACTOR_BASE_DATA) == 0x18, "layout");

// FactionRankArray: STANDIN GUESS(low); the community BSTArray<FACTION_RANK> modelled as its three header fields, the name is a low-confidence guess
// FreeFactions: GUESS(low); releases the array storage, target 0xce0ed0
struct FactionRankArray;
void FreeFactions(FactionRankArray* a_array);

struct FactionRankArray
{
	// Clear: GUESS(low); frees the storage when there is any and empties the array
	void Clear()
	{
		if (_data) {
			FreeFactions(this);
			_size = 0;
		}
	}

	void* _data;  // 00
	std::uint32_t _capacity;  // 08
	std::uint32_t _pad0C;  // 0C
	std::uint32_t _size;  // 10
	std::uint32_t _pad14;  // 14
};
static_assert(sizeof(FactionRankArray) == 0x18, "layout");

// TESActorBaseData: EXE_RTTI; class name and base from the image RTTI, 9 primary vftable slots
// sizeof TESActorBaseData 0x58: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESActorBaseData : public ::BaseFormComponent
{
public:
	// TESActorBaseData::~TESActorBaseData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1de460, inherited name
	~TESActorBaseData() override;  // 00
	// TESActorBaseData::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1dc5e0, inherited name
	void InitializeDataComponent() override;  // 01
	// TESActorBaseData::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1dc630, inherited name
	void ClearDataComponent() override;  // 02
	// TESActorBaseData::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1dc660, inherited name
	void CopyComponent() override;  // 03
	// TESActorBaseData::CopyFromTemplateForms: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x1de580
	virtual void CopyFromTemplateForms();  // 04
	// TESActorBaseData::GetIsGhost: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5, target 0x1de5d0
	virtual bool GetIsGhost() const;  // 05
	// TESActorBaseData::GetInvulnerable: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6, target 0x1de5c0
	virtual bool GetInvulnerable() const;  // 06
	// TESActorBaseData::Unk_07: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 7, target 0x1de5e0
	virtual bool Unk_07();  // 07
	// TESActorBaseData::GetVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 8, target 0x1de5f0
	virtual BGSVoiceType* GetVoiceType();  // 08

		// actorData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	ACTOR_BASE_DATA actorData;  // 08
	// deathItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESLevItem* deathItem;  // 20
	// voiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BGSVoiceType* voiceType;  // 28
	// baseTemplateForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); held as an opaque pointer
	void* baseTemplateForm;  // 30
	// unk38: GUESS(low); the community header declares TESForm** templateForms here, the target stores a dword
	std::uint32_t unk38;  // 38
	// unk3C: GUESS(low); upper half of the community templateForms pointer
	std::uint32_t unk3C;  // 3C
	// factions: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); BSTArray<FACTION_RANK> in the community header
	FactionRankArray factions;  // 40
};
static_assert(sizeof(TESActorBaseData) == 0x58, "layout");
