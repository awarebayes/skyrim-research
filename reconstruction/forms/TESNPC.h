// TESNPC type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESNPC.h
// and the vftables of the pinned image; the powerof3 fork (GPL-3.0) declares the same names.
// BaseFormComponent, TESForm, TESObject, TESBoundObject, TESBoundAnimObject, TESActorBase: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT);
// only class names, base chain, slot order and sizes are claimed; slot signatures other than the
// compared ones are placeholders. Member names carved out of the padding follow the same headers.
// BGSHeadPart, BGSVoiceType, BGSRelationship, TESRace, PlayerCharacter, HeadRelatedData, Sounds, FaceData, Layer, BSTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

class BGSVoiceType;
class PlayerCharacter;
class TESNPC;
class TESCombatStyle;

// BGSVoiceType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only named, never dereferenced
// TESRace: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the two height values GetScale reads
class TESRace
{
public:
	// unk00: GUESS(low); members not recovered yet
	std::uint8_t unk00[0xF8];  // 00
	// height: GUESS(low); male and female scale; the community header names the pair in the race data
	float height[2];  // F8
};

// BGSRelationship: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one member at 0x38
class BGSRelationship
{
public:
	// BGSRelationship::GetRelationship: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); target 0x3a5290, a static wrapper in the community header
	static BGSRelationship* GetRelationship(TESNPC* a_npc1, TESNPC* a_npc2);

	// unk00: GUESS(low); members not recovered yet
	std::uint8_t unk00[0x38];  // 00
	// rankBits: GUESS(low); the low 31 bits are the rank index
	std::uint32_t rankBits;  // 38
};

// BGSHeadPart: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only named
class BGSHeadPart;

// BSTArrayHeapAllocator, BSTArrayBase, BSTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout 0x18 as observed in the destructor
// BSTArrayHeapAllocator::~BSTArrayHeapAllocator: GUESS(low); target 0xce0f30
// BSTArrayHeapAllocator::Release: GUESS(low); target 0xce0ed0
// BSTArrayBase::~BSTArrayBase: GUESS(low); target 0xce0ca0
class BSTArrayHeapAllocator
{
public:
	~BSTArrayHeapAllocator();
	void Release();

	void*         data;      // 00
	std::uint32_t capacity;  // 08
	std::uint32_t pad0C;     // 0C
};

class BSTArrayBase
{
public:
	~BSTArrayBase();

	std::uint32_t size;  // 00
};

template <class T>
class BSTArray : public BSTArrayHeapAllocator, public BSTArrayBase
{
public:
	~BSTArray()
	{
		// the original destructor frees the storage when one is allocated
		if (data) {
			Release();
			size = 0;
		}
	}
};

// HeadRelatedData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 0x10 bytes, trivial
struct HeadRelatedData
{
	std::uint64_t unk00[2];  // 00
};
// Layer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 0xC bytes, trivial
struct Layer
{
	std::uint32_t unk00[3];  // 00
};
// FaceData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 0x5C bytes, trivial
struct FaceData
{
	std::uint8_t unk00[0x5C];  // 00
};
// Sounds: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 0x40 bytes
// Sounds::~Sounds: GUESS(low); target 0x3aee80
struct Sounds
{
	~Sounds();

	std::uint8_t unk00[0x40];  // 00
};

// OverlayEntry: GUESS(low); one 0x18-byte slot of the base-overlay hash table, keyed by NPC
// OverlayEntry::next is null for an empty slot; the chain ends at the sentinel pointer
struct OverlayEntry
{
	const void*             key;    // 00
	BSTArray<BGSHeadPart*>* value;  // 08
	OverlayEntry*           next;   // 10
};
// g_overlayEntries, g_overlayCapacity, g_overlaySentinel: GUESS(low); globals at 0x209c8e0, 0x209c8c4 and 0x209c8d0
extern OverlayEntry*  g_overlayEntries;
extern std::uint32_t  g_overlayCapacity;
extern OverlayEntry*  g_overlaySentinel;

// CRC32Calculator::SizeOf64: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); target 0xce25f0
class CRC32Calculator
{
public:
	static void SizeOf64(std::uint32_t& a_crc, std::uint64_t a_data);
};

// GetPlayerBaseNPC: GUESS(low); target 0x69dcd0, returns the key the overlay table uses for the player
const void* GetPlayerBaseNPC(PlayerCharacter* a_player);

// PlayerCharacter: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class PlayerCharacter
{
public:
	// singleton: GUESS; the global at 0x3230778, which NG reads through PlayerCharacter::GetSingleton
	static PlayerCharacter* singleton;

	// unk00: OBSERVED; placeholder named by its offset, members not recovered yet (not the nested unk00 members of NG)
	std::uint8_t unk00[0xB48];  // 00
	// unkB48: OBSERVED; placeholder named by its offset, a race pointer compared with TESRaceForm::race (NG's runtime data has an int32 unkB48 here, not taken to be this member)
	TESRace* unkB48;  // B48
};

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x146610
	// community declaration: virtual ~BaseFormComponent();
	virtual ~BaseFormComponent();  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x15a97c8
	// community declaration: virtual void InitializeDataComponent() = 0;
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x15a97c8
	// community declaration: virtual void ClearDataComponent() = 0;
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x145470
	// community declaration: virtual void CopyComponent(BaseFormComponent* a_rhs);
	virtual void CopyComponent();  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");

// TESForm: STANDIN EXE_RTTI; class name and base from the image RTTI, 59 primary vftable slots
class TESForm : public ::BaseFormComponent
{
public:
	// TESForm::~TESForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x1e7910, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESForm() override;  // 00
	// TESForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x1e35c0, inherited name
	// community declaration: virtual void InitializeDataComponent() = 0;
	void InitializeDataComponent() override;  // 01
	// TESForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x1e36c0, inherited name
	// community declaration: virtual void ClearDataComponent() = 0;
	void ClearDataComponent() override;  // 02
	// TESForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1e6930, inherited name
	// community declaration: virtual void CopyComponent(BaseFormComponent* a_rhs);
	void CopyComponent() override;  // 03
	// TESForm::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x1e35b0
	// community declaration: virtual void InitializeData();
	virtual void InitializeData();  // 04
	// TESForm::ClearData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5, target 0x1e36b0
	// community declaration: virtual void ClearData();
	virtual void ClearData();  // 05
	// TESForm::Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6, target 0x1c7e90
	// community declaration: virtual bool Load(TESFile* a_mod);
	virtual void Load();  // 06
	// TESForm::LoadPartial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 7, target 0x1469b0
	// community declaration: virtual bool LoadPartial(TESFile* a_mod);
	virtual void LoadPartial();  // 07
	// TESForm::LoadEdit: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 8, target 0x1469a0
	// community declaration: virtual bool LoadEdit(TESFile* a_mod);
	virtual void LoadEdit();  // 08
	// TESForm::CreateDuplicateForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 9, target 0x1e51a0
	// community declaration: virtual TESForm* CreateDuplicateForm(bool a_createEditorID, void* a_arg2);
	virtual void CreateDuplicateForm();  // 09
	// TESForm::AddChange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 10, target 0x1e5650
	// community declaration: virtual bool AddChange(std::uint32_t a_changeFlags);
	virtual void AddChange();  // 0A
	// TESForm::RemoveChange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 11, target 0x1e56b0
	// community declaration: virtual void RemoveChange(std::uint32_t a_changeFlags);
	virtual void RemoveChange();  // 0B
	// TESForm::FindInFileFast: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 12, target 0x1e56e0
	// community declaration: virtual bool FindInFileFast(TESFile* a_mod);
	virtual void FindInFileFast();  // 0C
	// TESForm::CheckSaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 13, target 0x1e56f0
	// community declaration: virtual bool CheckSaveGame(BGSSaveFormBuffer* a_buf);
	virtual void CheckSaveGame();  // 0D
	// TESForm::SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 14, target 0x1e5700
	// community declaration: virtual void SaveGame(BGSSaveFormBuffer* a_buf);
	virtual void SaveGame();  // 0E
	// TESForm::LoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 15, target 0x1e5770
	// community declaration: virtual void LoadGame(BGSLoadFormBuffer* a_buf);
	virtual void LoadGame();  // 0F
	// TESForm::InitLoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 16, target 0x1e5830
	// community declaration: virtual void InitLoadGame(BGSLoadFormBuffer* a_buf);
	virtual void InitLoadGame();  // 10
	// TESForm::FinishLoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 17, target 0x1e5840
	// community declaration: virtual void FinishLoadGame(BGSLoadFormBuffer* a_buf);
	virtual void FinishLoadGame();  // 11
	// TESForm::Revert: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 18, target 0x1e5850
	// community declaration: virtual void Revert(BGSLoadFormBuffer* a_buf);
	virtual void Revert();  // 12
	// TESForm::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 19, target 0x1c7db0
	// community declaration: virtual void InitItemImpl();
	virtual void InitItemImpl();  // 13
	// TESForm::GetDescriptionOwnerFile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 20, target 0x1466f0
	// community declaration: [[nodiscard]] virtual TESFile* GetDescriptionOwnerFile() const;
	virtual void GetDescriptionOwnerFile();  // 14
	// TESForm::GetSavedFormType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 21, target 0x146820
	// community declaration: [[nodiscard]] virtual FormType GetSavedFormType() const;
	virtual void GetSavedFormType();  // 15
	// TESForm::GetFormDetailedString: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 22, target 0x1e5d10
	// community declaration: virtual void GetFormDetailedString(char* a_buf, std::uint32_t a_bufLen);
	virtual void GetFormDetailedString();  // 16
	// TESForm::GetKnown: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 23, target 0x146750
	// community declaration: [[nodiscard]] virtual bool GetKnown() const;
	virtual void GetKnown();  // 17
	// TESForm::GetRandomAnim: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0x146800
	// community declaration: [[nodiscard]] virtual bool GetRandomAnim() const;
	virtual void GetRandomAnim();  // 18
	// TESForm::GetPlayable: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0x1467f0
	// community declaration: [[nodiscard]] virtual bool GetPlayable() const;
	virtual void GetPlayable();  // 19
	// TESForm::IsHeadingMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0x1467a0
	// community declaration: [[nodiscard]] virtual bool IsHeadingMarker() const;
	virtual void IsHeadingMarker();  // 1A
	// TESForm::GetDangerous: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0x1466a0
	// community declaration: [[nodiscard]] virtual bool GetDangerous() const;
	virtual void GetDangerous();  // 1B
	// TESForm::QHasCurrents: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0x146a10
	// community declaration: [[nodiscard]] virtual bool QHasCurrents() const;
	virtual void QHasCurrents();  // 1C
	// TESForm::GetObstacle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0x1467d0
	// community declaration: [[nodiscard]] virtual bool GetObstacle() const;
	virtual void GetObstacle();  // 1D
	// TESForm::QIsLODLandObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 30, target 0x146a20
	// community declaration: [[nodiscard]] virtual bool QIsLODLandObject() const;
	virtual void QIsLODLandObject();  // 1E
	// TESForm::GetOnLocalMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 31, target 0x1467e0
	// community declaration: [[nodiscard]] virtual bool GetOnLocalMap() const;
	virtual void GetOnLocalMap();  // 1F
	// TESForm::GetMustUpdate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 32, target 0x146790
	// community declaration: [[nodiscard]] virtual bool GetMustUpdate() const;
	virtual void GetMustUpdate();  // 20
	// TESForm::SetOnLocalMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 33, target 0x1e5fd0
	// community declaration: virtual void SetOnLocalMap(bool a_set);
	virtual void SetOnLocalMap();  // 21
	// TESForm::GetIgnoredBySandbox: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 34, target 0x146740
	// community declaration: [[nodiscard]] virtual bool GetIgnoredBySandbox() const;
	virtual void GetIgnoredBySandbox();  // 22
	// TESForm::SetDelete: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 35, target 0x1e6070
	// community declaration: virtual void SetDelete(bool a_set);
	virtual void SetDelete();  // 23
	// TESForm::SetAltered: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 36, target 0x1e60d0
	// community declaration: virtual void SetAltered(bool a_set);
	virtual void SetAltered();  // 24
	// TESForm::SaveObjectBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 37, target 0x146a30
	// community declaration: virtual void SaveObjectBound();
	virtual void SaveObjectBound();  // 25
	// TESForm::LoadObjectBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 38, target 0x14c900
	// community declaration: virtual void LoadObjectBound(TESFile* a_mod);
	virtual void LoadObjectBound();  // 26
	// TESForm::IsBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 39, target 0x14c8e0
	// community declaration: [[nodiscard]] virtual bool IsBoundObject() const;
	virtual void IsBoundObject();  // 27
	// TESForm::IsObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 40, target 0x14c8f0
	// community declaration: [[nodiscard]] virtual bool IsObject() const;
	virtual void IsObject();  // 28
	// TESForm::IsMagicItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 41, target 0x147560
	// community declaration: [[nodiscard]] virtual bool IsMagicItem() const;
	virtual void IsMagicItem();  // 29
	// TESForm::IsWater: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 42, target 0x146980
	// community declaration: [[nodiscard]] virtual bool IsWater() const;
	virtual void IsWater();  // 2A
	// TESForm::AsReference1: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 43, target 0x146970
	// community declaration: virtual TESObjectREFR* AsReference1();
	virtual void AsReference1();  // 2B
	// TESForm::AsReference2: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 44, target 0x146960
	// community declaration: [[nodiscard]] virtual const TESObjectREFR* AsReference2() const;
	virtual void AsReference2();  // 2C
	// TESForm::GetRefCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 45, target 0x14c8d0
	// community declaration: [[nodiscard]] virtual std::uint32_t GetRefCount() const;
	virtual void GetRefCount();  // 2D
	// TESForm::GetTextForParsedSubTag: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 46, target 0x1e68f0
	// community declaration: [[nodiscard]] virtual const char* GetTextForParsedSubTag(const BSFixedString& a_tag) const;
	virtual void GetTextForParsedSubTag();  // 2E
	// TESForm::Copy: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 47, target 0x1e6920
	// community declaration: virtual void Copy(TESForm* a_srcForm);
	virtual void Copy();  // 2F
	// TESForm::BelongsInGroup: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 48, target 0x1e6ab0
	// community declaration: virtual bool BelongsInGroup(FORM* a_form, bool a_allowParentGroups, bool a_currentOnly);
	virtual void BelongsInGroup();  // 30
	// TESForm::CreateGroupData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 49, target 0x1e6b00
	// community declaration: virtual void CreateGroupData(FORM* a_form, FORM_GROUP* a_group);
	virtual void CreateGroupData();  // 31
	// TESForm::GetFormEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 50, target 0x146710
	// community declaration: [[nodiscard]] virtual const char* GetFormEditorID() const;
	virtual void GetFormEditorID();  // 32
	// TESForm::SetFormEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 51, target 0x146a60
	// community declaration: virtual bool SetFormEditorID(const char* a_str);
	virtual void SetFormEditorID();  // 33
	// TESForm::IsParentForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 52, target 0x1e6b40
	// community declaration: virtual bool IsParentForm();
	virtual void IsParentForm();  // 34
	// TESForm::IsParentFormTree: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 53, target 0x1e6b50
	// community declaration: virtual bool IsParentFormTree();
	virtual void IsParentFormTree();  // 35
	// TESForm::IsFormTypeChild: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 54, target 0x1468f0
	// community declaration: virtual bool IsFormTypeChild(FormType a_type);
	virtual void IsFormTypeChild();  // 36
	// TESForm::Activate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 55, target 0x14c860
	// community declaration: virtual bool Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t
	virtual void Activate();  // 37
	// TESForm::SetFormID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 56, target 0x1e6bd0
	// community declaration: virtual void SetFormID(FormID a_id, bool a_updateFile);
	virtual void SetFormID();  // 38
	// TESForm::GetObjectTypeName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 57, target 0x1467b0
	// community declaration: [[nodiscard]] virtual const char* GetObjectTypeName() const;
	virtual void GetObjectTypeName();  // 39
	// TESForm::QAvailableInGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 58, target 0x146a00
	// community declaration: [[nodiscard]] virtual bool QAvailableInGame() const;
	virtual void QAvailableInGame();  // 3A
};

// TESObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 72 primary vftable slots
// sizeof TESObject 0x20: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESObject : public ::TESForm
{
public:
	// TESObject::~TESObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x2791c0, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESObject() override;  // 00
	// TESObject::IsObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 40, target 0x146930, inherited name
	// community declaration: [[nodiscard]] virtual bool IsObject() const;
	void IsObject() override;  // 28
	// TESObject::GetRefCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 45, target 0x146810, inherited name
	// community declaration: [[nodiscard]] virtual std::uint32_t GetRefCount() const;
	void GetRefCount() override;  // 2D
	// TESObject::Unk_3B: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 59, target 0x146990
	// community declaration: virtual void Unk_3B(void);
	virtual void Unk_3B();  // 3B
	// TESObject::IsBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 60, target 0x146890
	// community declaration: virtual bool IsBoundAnimObject();
	virtual void IsBoundAnimObject();  // 3C
	// TESObject::GetWaterType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 61, target 0x146840
	// community declaration: [[nodiscard]] virtual TESWaterForm* GetWaterType() const;
	virtual void GetWaterType();  // 3D
	// TESObject::IsAutoCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 62, target 0x147550
	// community declaration: [[nodiscard]] virtual bool IsAutoCalc() const;
	virtual void IsAutoCalc();  // 3E
	// TESObject::SetAutoCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 63, target 0x146a40
	// community declaration: virtual void SetAutoCalc(bool a_autoCalc);
	virtual void SetAutoCalc();  // 3F
	// TESObject::Clone3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 64, target 0x275b50
	// community declaration: virtual NiAVObject* Clone3D(TESObjectREFR* a_ref, bool a_arg3);
	virtual void Clone3D();  // 40
	// TESObject::UnClone3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 65, target 0x275b60
	// community declaration: virtual void UnClone3D(TESObjectREFR* a_ref);
	virtual void UnClone3D();  // 41
	// TESObject::IsMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 66, target 0x275e10
	// community declaration: virtual bool IsMarker();
	virtual void IsMarker();  // 42
	// TESObject::IsOcclusionMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 67, target 0x275ee0
	// community declaration: virtual bool IsOcclusionMarker();
	virtual void IsOcclusionMarker();  // 43
	// TESObject::ReplaceModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 68, target 0x275f10
	// community declaration: virtual bool ReplaceModel();
	virtual void ReplaceModel();  // 44
	// TESObject::IncRef: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 69, target 0x146860
	// community declaration: virtual std::uint32_t IncRef();
	virtual void IncRef();  // 45
	// TESObject::DecRef: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 70, target 0x146640
	// community declaration: virtual std::uint32_t DecRef();
	virtual void DecRef();  // 46
	// TESObject::LoadGraphics: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 71, target 0x276430
	// community declaration: virtual NiAVObject* LoadGraphics(TESObjectREFR* a_ref);
	virtual void LoadGraphics();  // 47

	// unk08: GUESS(low); members not recovered yet
	std::uint8_t unk08[0x08];  // 08
	// formFlags, formID, formType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); TESForm members at 10, 14 and 1A, held here because the stand-in TESForm has no members
	std::uint32_t formFlags;  // 10
	std::uint32_t formID;     // 14
	// unk18: GUESS(low); inGameFormFlags in the community header
	std::uint16_t unk18;  // 18
	std::uint8_t  formType;  // 1A
	// unk1B: GUESS(low); padding
	std::uint8_t  unk1B;  // 1B
	std::uint32_t unk1C;  // 1C
};
static_assert(sizeof(TESObject) == 0x20, "layout");

// TESBoundObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 83 primary vftable slots
// sizeof TESBoundObject 0x30: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESBoundObject : public ::TESObject
{
public:
	// TESBoundObject::~TESBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x279180, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESBoundObject() override;  // 00
	// TESBoundObject::LoadObjectBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 38, target 0x277b10, inherited name
	// community declaration: virtual void LoadObjectBound(TESFile* a_mod);
	void LoadObjectBound() override;  // 26
	// TESBoundObject::IsBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 39, target 0x1468a0, inherited name
	// community declaration: [[nodiscard]] virtual bool IsBoundObject() const;
	void IsBoundObject() override;  // 27
	// TESBoundObject::Activate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 55, target 0x278e50, inherited name
	// community declaration: virtual bool Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t
	void Activate() override;  // 37
	// TESBoundObject::Clone3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 64, target 0x277e20, inherited name
	// community declaration: virtual NiAVObject* Clone3D(TESObjectREFR* a_ref, bool a_arg3);
	void Clone3D() override;  // 40
	// TESBoundObject::ReplaceModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 68, target 0x278e00, inherited name
	// community declaration: virtual bool ReplaceModel();
	void ReplaceModel() override;  // 44
	// TESBoundObject::SetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 72, target 0x146a70
	// community declaration: virtual void SetObjectVoiceType(BGSVoiceType* a_voiceType);
	virtual void SetObjectVoiceType(BGSVoiceType* a_voiceType);  // 48
	// TESBoundObject::GetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 73, target 0x1467c0
	// community declaration: [[nodiscard]] virtual BGSVoiceType* GetObjectVoiceType() const;
	virtual void GetObjectVoiceType();  // 49
	// TESBoundObject::Clone3D_4A: GUESS; the community name repeats at another slot, suffixed with this slot
	// community declaration: virtual NiAVObject* Clone3D(TESObjectREFR* a_ref);
	virtual void Clone3D_4A();  // 4A
	// TESBoundObject::ReplaceModel_4B: GUESS; the community name repeats at another slot, suffixed with this slot
	// community declaration: virtual bool ReplaceModel(const char* a_str);
	virtual void ReplaceModel_4B();  // 4B
	// TESBoundObject::GetActivateText: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 76, target 0x278ed0
	// community declaration: virtual bool GetActivateText(TESObjectREFR* a_activator, BSString& a_dst);
	virtual void GetActivateText();  // 4C
	// TESBoundObject::CalculateDoFavor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 77, target 0x278f90
	// community declaration: virtual bool CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3);
	virtual void CalculateDoFavor();  // 4D
	// TESBoundObject::HandleRemoveItemFromContainer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 78, target 0x146850
	// community declaration: virtual void HandleRemoveItemFromContainer(TESObjectREFR* a_container);
	virtual void HandleRemoveItemFromContainer();  // 4E
	// TESBoundObject::OnRemove3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 79, target 0x1469f0
	// community declaration: virtual void OnRemove3D(NiAVObject* a_obj3D);
	virtual void OnRemove3D();  // 4F
	// TESBoundObject::OnCheckModels: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 80, target 0x1469c0
	// community declaration: virtual void OnCheckModels();
	virtual void OnCheckModels();  // 50
	// TESBoundObject::OnCopyReference: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 81, target 0x1469d0
	// community declaration: virtual void OnCopyReference();
	virtual void OnCopyReference();  // 51
	// TESBoundObject::OnFinishScale: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 82, target 0x1469e0
	// community declaration: virtual void OnFinishScale();
	virtual void OnFinishScale();  // 52

	// unk20: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk20[0x10];  // 20
};
static_assert(sizeof(TESBoundObject) == 0x30, "layout");

// TESBoundAnimObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 83 primary vftable slots
// sizeof TESBoundAnimObject 0x30: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESBoundAnimObject : public ::TESBoundObject
{
public:
	// TESBoundAnimObject::~TESBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x279140, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESBoundAnimObject() override;  // 00
	// TESBoundAnimObject::IsBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 60, target 0x267800, inherited name
	// community declaration: virtual bool IsBoundAnimObject();
	void IsBoundAnimObject() override;  // 3C
	// TESBoundAnimObject::ReplaceModel_4B: GUESS; the community name repeats at another slot, suffixed with this slot
	// community declaration: virtual bool ReplaceModel(const char* a_str);
	void ReplaceModel_4B() override;  // 4B
};
static_assert(sizeof(TESBoundAnimObject) == 0x30, "layout");

// TESActorBase: STANDIN EXE_RTTI; class name and base from the image RTTI, 87 primary vftable slots
// sizeof TESActorBase 0x150: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// Other RTTI bases (not declared here; their vftable pointers lie inside the members): .?AVTESActorBaseData@@, .?AVTESContainer@@, .?AVTESSpellList@@, .?AVTESAIForm@@, .?AVTESFullName@@, .?AVActorValueOwner@@, .?AVBGSDestructibleObjectForm@@, .?AVBGSSkinForm@@, .?AVBGSKeywordForm@@, .?AVBGSAttackDataForm@@, .?AVBGSPerkRankArray@@
class TESActorBase : public ::TESBoundAnimObject
{
public:
	// TESActorBase::~TESActorBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x3cbc60, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESActorBase() override;  // 00
	// TESActorBase::AddChange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 10, target 0x3b0460, inherited name
	// community declaration: virtual bool AddChange(std::uint32_t a_changeFlags);
	void AddChange() override;  // 0A
	// TESActorBase::RemoveChange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 11, target 0x3b04e0, inherited name
	// community declaration: virtual void RemoveChange(std::uint32_t a_changeFlags);
	void RemoveChange() override;  // 0B
	// TESActorBase::SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 14, target 0x3b0550, inherited name
	// community declaration: virtual void SaveGame(BGSSaveFormBuffer* a_buf);
	void SaveGame() override;  // 0E
	// TESActorBase::LoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 15, target 0x3b05d0, inherited name
	// community declaration: virtual void LoadGame(BGSLoadFormBuffer* a_buf);
	void LoadGame() override;  // 0F
	// TESActorBase::Revert: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 18, target 0x3b06a0, inherited name
	// community declaration: virtual void Revert(BGSLoadFormBuffer* a_buf);
	void Revert() override;  // 12
	// TESActorBase::IsAutoCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 62, target 0x3afed0, inherited name
	// community declaration: [[nodiscard]] virtual bool IsAutoCalc() const;
	void IsAutoCalc() override;  // 3E
	// TESActorBase::SetAutoCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 63, target 0x3afef0, inherited name
	// community declaration: virtual void SetAutoCalc(bool a_autoCalc);
	void SetAutoCalc() override;  // 3F
	// TESActorBase::GetHasPLSpecTex: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 83, target 0x3cc6d0
	// community declaration: [[nodiscard]] virtual bool GetHasPLSpecTex() const;
	virtual void GetHasPLSpecTex();  // 53
	// TESActorBase::GetCombatStyle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 84, target 0x3cc650
	// community declaration: virtual TESCombatStyle* GetCombatStyle();
	virtual TESCombatStyle* GetCombatStyle();  // 54
	// TESActorBase::SetCombatStyle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 85, target 0x3cd8c0
	// community declaration: virtual void SetCombatStyle(TESCombatStyle* a_combatStyle);
	virtual void SetCombatStyle(TESCombatStyle* a_combatStyle);  // 55
	// TESActorBase::GetAsForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 86, target 0x3cc620
	// community declaration: virtual TESForm* GetAsForm();
	virtual void GetAsForm();  // 56

	// unk30: GUESS(low); the TESActorBaseData vftable pointer and the members before the flags
	std::uint8_t unk30[0x08];  // 30
	// actorBaseFlags: GUESS(low); the community header holds it as TESActorBaseData::actorData.actorBaseFlags
	std::uint32_t actorBaseFlags;  // 38
	// unk3C: GUESS(low); members not recovered yet
	std::uint8_t unk3C[0x1C];  // 3C
	// voiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); TESActorBaseData::voiceType
	BGSVoiceType* voiceType;  // 58
	// unk60: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk60[0xF0];  // 60
};
static_assert(sizeof(TESActorBase) == 0x150, "layout");

// TESNPC: EXE_RTTI; class name and base from the image RTTI, 87 primary vftable slots
// Other RTTI bases (not declared here; their vftable pointers lie inside the members): .?AVTESActorBaseData@@, .?AVTESContainer@@, .?AVTESSpellList@@, .?AVTESAIForm@@, .?AVTESFullName@@, .?AVActorValueOwner@@, .?AVBGSDestructibleObjectForm@@, .?AVBGSSkinForm@@, .?AVBGSKeywordForm@@, .?AVBGSAttackDataForm@@, .?AVBGSPerkRankArray@@, .?AVTESRaceForm@@, .?AVBGSOverridePackCollection@@, .?AV?$BSTEventSink@VMenuOpenCloseEvent@@@@
class TESNPC : public ::TESActorBase
{
public:
	// TESNPC::~TESNPC: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x3cbca0, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESNPC() override;  // 00
	// TESNPC::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x3bbd80, inherited name
	// community declaration: virtual void InitializeData();
	void InitializeData() override;  // 04
	// TESNPC::ClearData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5, target 0x3bbf50, inherited name
	// community declaration: virtual void ClearData();
	void ClearData() override;  // 05
	// TESNPC::Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6, target 0x3bc130, inherited name
	// community declaration: virtual bool Load(TESFile* a_mod);
	void Load() override;  // 06
	// TESNPC::FindInFileFast: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 12, target 0x3c8570, inherited name
	// community declaration: virtual bool FindInFileFast(TESFile* a_mod);
	void FindInFileFast() override;  // 0C
	// TESNPC::SaveGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 14, target 0x3c7640, inherited name
	// community declaration: virtual void SaveGame(BGSSaveFormBuffer* a_buf);
	void SaveGame() override;  // 0E
	// TESNPC::LoadGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 15, target 0x3c7b10, inherited name
	// community declaration: virtual void LoadGame(BGSLoadFormBuffer* a_buf);
	void LoadGame() override;  // 0F
	// TESNPC::Revert: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 18, target 0x3c8410, inherited name
	// community declaration: virtual void Revert(BGSLoadFormBuffer* a_buf);
	void Revert() override;  // 12
	// TESNPC::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 19, target 0x3c1570, inherited name
	// community declaration: virtual void InitItemImpl();
	void InitItemImpl() override;  // 13
	// TESNPC::GetTextForParsedSubTag: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 46, target 0x3c74a0, inherited name
	// community declaration: [[nodiscard]] virtual const char* GetTextForParsedSubTag(const BSFixedString& a_tag) const;
	void GetTextForParsedSubTag() override;  // 2E
	// TESNPC::Copy: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 47, target 0x3bdd00, inherited name
	// community declaration: virtual void Copy(TESForm* a_srcForm);
	void Copy() override;  // 2F
	// TESNPC::Activate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 55, target 0x3c05c0, inherited name
	// community declaration: virtual bool Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t
	void Activate() override;  // 37
	// TESNPC::UnClone3D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 65, target 0x3c28b0, inherited name
	// community declaration: virtual void UnClone3D(TESObjectREFR* a_ref);
	void UnClone3D() override;  // 41
	// TESNPC::SetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 72, target 0x3cd8d0, inherited name
	// community declaration: virtual void SetObjectVoiceType(BGSVoiceType* a_voiceType);
	void SetObjectVoiceType(BGSVoiceType* a_voiceType) override;  // 48
	// TESNPC::GetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 73, target 0x3c6630, inherited name
	// community declaration: [[nodiscard]] virtual BGSVoiceType* GetObjectVoiceType() const;
	void GetObjectVoiceType() override;  // 49
	// TESNPC::Clone3D_4A: GUESS; the community name repeats at another slot, suffixed with this slot
	// community declaration: virtual NiAVObject* Clone3D(TESObjectREFR* a_ref);
	void Clone3D_4A() override;  // 4A
	// TESNPC::GetActivateText: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 76, target 0x3c1000, inherited name
	// community declaration: virtual bool GetActivateText(TESObjectREFR* a_activator, BSString& a_dst);
	void GetActivateText() override;  // 4C
	// TESNPC::CalculateDoFavor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 77, target 0x3c13d0, inherited name
	// community declaration: virtual bool CalculateDoFavor(Actor* a_activator, bool a_arg2, TESObjectREFR* a_toActivate, float a_arg3);
	void CalculateDoFavor() override;  // 4D
	// TESNPC::GetCombatStyle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 84, target 0x3c6150, inherited name
	// community declaration: virtual TESCombatStyle* GetCombatStyle();
	TESCombatStyle* GetCombatStyle() override;  // 54
	// TESNPC::SetCombatStyle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 85, target 0x3c9100, inherited name
	// community declaration: virtual void SetCombatStyle(TESCombatStyle* a_combatStyle);
	void SetCombatStyle(TESCombatStyle* a_combatStyle) override;  // 55

	// TESNPC::IsFemale: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); target 0x3afeb0
	std::int32_t IsFemale();
	// TESNPC::GetRelationshipRankIndex: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); target 0x3a4e00
	static std::int32_t GetRelationshipRankIndex(TESNPC* a_npc1, TESNPC* a_npc2);
	// TESNPC::GetScale: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); target 0x3c65c0
	float GetScale();
	// TESNPC::HasOverlays: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); target 0x3c8c00
	bool HasOverlays();

	// unk150: GUESS(low); the TESRaceForm vftable pointer
	std::uint8_t unk150[0x08];  // 150
	// race: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); TESRaceForm::race
	TESRace* race;  // 158
	// unk160: GUESS(low); members not recovered yet
	std::uint8_t unk160[0x68];  // 160
	// headRelatedData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	HeadRelatedData* headRelatedData;  // 1C8
	// unk1D0: GUESS(low); members not recovered yet
	std::uint8_t unk1D0[0x8];  // 1D0
    // combatStyle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the pointer at 0x1D8 that both combat style accessors read and write, name as reported by the label check
    TESCombatStyle* combatStyle;  // 1D8
    // unk1E0: GUESS(low); padding up to originalRace
    std::uint8_t unk1E0[0x8];  // 1E0
	// originalRace: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESRace* originalRace;  // 1E8
	// unk1F0: GUESS(low); faceNPC in the community header
	std::uint8_t unk1F0[0x08];  // 1F0
	// height: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	float height;  // 1F8
	// unk1FC: GUESS(low); weight in the community header
	std::uint32_t unk1FC;  // 1FC
	// sounds: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); a pointer here, the community type name is Sounds
	Sounds* sounds;  // 200
	// unk208: GUESS(low); members not recovered yet
	std::uint8_t unk208[0x48];  // 208
	// relationships: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BSTArray<BGSRelationship*>* relationships;  // 250
	// faceData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	FaceData* faceData;  // 258
	// tintLayers: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BSTArray<Layer*>* tintLayers;  // 260
};
