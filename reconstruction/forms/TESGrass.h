// TESGrass type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESGrass.h
// and the vftables of the pinned image; the powerof3 fork (GPL-3.0) declares the same names.
// BaseFormComponent, TESForm, TESObject, TESBoundObject, TESModel: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT);
// only class names, base chain, slot order and sizes are claimed; slot signatures other than
// TESGrass's compared ones are placeholders.
#pragma once

#include <cstdint>

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
static_assert((sizeof(BaseFormComponent) == 0x8), "layout");

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
	// community declaration: virtual TESFile* GetDescriptionOwnerFile() const;
	virtual void GetDescriptionOwnerFile();  // 14
	// TESForm::GetSavedFormType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 21, target 0x146820
	// community declaration: virtual FormType GetSavedFormType() const;
	virtual void GetSavedFormType();  // 15
	// TESForm::GetFormDetailedString: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 22, target 0x1e5d10
	// community declaration: virtual void GetFormDetailedString(char* a_buf, std::uint32_t a_bufLen);
	virtual void GetFormDetailedString();  // 16
	// TESForm::GetKnown: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 23, target 0x146750
	// community declaration: virtual bool GetKnown() const;
	virtual void GetKnown();  // 17
	// TESForm::GetRandomAnim: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0x146800
	// community declaration: virtual bool GetRandomAnim() const;
	virtual void GetRandomAnim();  // 18
	// TESForm::GetPlayable: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0x1467f0
	// community declaration: virtual bool GetPlayable() const;
	virtual void GetPlayable();  // 19
	// TESForm::IsHeadingMarker: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0x1467a0
	// community declaration: virtual bool IsHeadingMarker() const;
	virtual void IsHeadingMarker();  // 1A
	// TESForm::GetDangerous: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0x1466a0
	// community declaration: virtual bool GetDangerous() const;
	virtual void GetDangerous();  // 1B
	// TESForm::QHasCurrents: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0x146a10
	// community declaration: virtual bool QHasCurrents() const;
	virtual void QHasCurrents();  // 1C
	// TESForm::GetObstacle: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0x1467d0
	// community declaration: virtual bool GetObstacle() const;
	virtual void GetObstacle();  // 1D
	// TESForm::QIsLODLandObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 30, target 0x146a20
	// community declaration: virtual bool QIsLODLandObject() const;
	virtual void QIsLODLandObject();  // 1E
	// TESForm::GetOnLocalMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 31, target 0x1467e0
	// community declaration: virtual bool GetOnLocalMap() const;
	virtual void GetOnLocalMap();  // 1F
	// TESForm::GetMustUpdate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 32, target 0x146790
	// community declaration: virtual bool GetMustUpdate() const;
	virtual void GetMustUpdate();  // 20
	// TESForm::SetOnLocalMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 33, target 0x1e5fd0
	// community declaration: virtual void SetOnLocalMap(bool a_set);
	virtual void SetOnLocalMap();  // 21
	// TESForm::GetIgnoredBySandbox: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 34, target 0x146740
	// community declaration: virtual bool GetIgnoredBySandbox() const;
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
	// community declaration: virtual bool IsBoundObject() const;
	virtual void IsBoundObject();  // 27
	// TESForm::IsObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 40, target 0x14c8f0
	// community declaration: virtual bool IsObject() const;
	virtual void IsObject();  // 28
	// TESForm::IsMagicItem: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 41, target 0x147560
	// community declaration: virtual bool IsMagicItem() const;
	virtual void IsMagicItem();  // 29
	// TESForm::IsWater: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 42, target 0x146980
	// community declaration: virtual bool IsWater() const;
	virtual void IsWater();  // 2A
	// TESForm::AsReference1: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 43, target 0x146970
	// community declaration: virtual TESObjectREFR* AsReference1();
	virtual void AsReference1();  // 2B
	// TESForm::AsReference2: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 44, target 0x146960
	// community declaration: virtual const TESObjectREFR* AsReference2() const;
	virtual void AsReference2();  // 2C
	// TESForm::GetRefCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 45, target 0x14c8d0
	// community declaration: virtual std::uint32_t GetRefCount() const;
	virtual void GetRefCount();  // 2D
	// TESForm::GetTextForParsedSubTag: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 46, target 0x1e68f0
	// community declaration: virtual const char* GetTextForParsedSubTag(const BSFixedString& a_tag) const;
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
	// community declaration: virtual const char* GetFormEditorID() const;
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
	// community declaration: virtual const char* GetObjectTypeName() const;
	virtual void GetObjectTypeName();  // 39
	// TESForm::QAvailableInGame: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 58, target 0x146a00
	// community declaration: virtual bool QAvailableInGame() const;
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
	// community declaration: virtual bool IsObject() const;
	void IsObject() override;  // 28
	// TESObject::GetRefCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 45, target 0x146810, inherited name
	// community declaration: virtual std::uint32_t GetRefCount() const;
	void GetRefCount() override;  // 2D
	// TESObject::Unk_3B: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 59, target 0x146990
	// community declaration: virtual void Unk_3B(void);
	virtual void Unk_3B();  // 3B
	// TESObject::IsBoundAnimObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 60, target 0x146890
	// community declaration: virtual bool IsBoundAnimObject();
	virtual void IsBoundAnimObject();  // 3C
	// TESObject::GetWaterType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 61, target 0x146840
	// community declaration: virtual TESWaterForm* GetWaterType() const;
	virtual void GetWaterType();  // 3D
	// TESObject::IsAutoCalc: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 62, target 0x147550
	// community declaration: virtual bool IsAutoCalc() const;
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

	// unk08: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk08[0x18];  // 08
};
static_assert((sizeof(TESObject) == 0x20), "layout");

// TESBoundObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 83 primary vftable slots
// sizeof TESBoundObject 0x30: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class TESBoundObject : public ::TESObject
{
public:
	TESBoundObject();
	// TESBoundObject::~TESBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x279180, inherited name
	// community declaration: virtual ~BaseFormComponent();
	~TESBoundObject() override;  // 00
	// TESBoundObject::LoadObjectBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 38, target 0x277b10, inherited name
	// community declaration: virtual void LoadObjectBound(TESFile* a_mod);
	void LoadObjectBound() override;  // 26
	// TESBoundObject::IsBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 39, target 0x1468a0, inherited name
	// community declaration: virtual bool IsBoundObject() const;
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
	virtual void SetObjectVoiceType();  // 48
	// TESBoundObject::GetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 73, target 0x1467c0
	// community declaration: virtual BGSVoiceType* GetObjectVoiceType() const;
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
static_assert((sizeof(TESBoundObject) == 0x30), "layout");

// TESModel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); name from NG, vftable 0x1812190 (7 slots) and
// base from the image RTTI; the layout after the vptr is not claimed beyond the NG size 0x28
// TESModel::unk08: GUESS(low); NG members model, textures, addons, numTextures, numAddons are not needed here
class TESModel : public ::BaseFormComponent
{
public:
	TESModel();
	~TESModel() override;  // 00
	void InitializeDataComponent() override;  // 01
	void ClearDataComponent() override;  // 02
	void CopyComponent() override;  // 03
	// TESModel::GetModel, SetModel, GetAsModelTextureSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	virtual void GetModel();  // 04
	virtual void SetModel();  // 05
	virtual void GetAsModelTextureSwap();  // 06

	std::uint8_t unk08[0x20];  // 08
};
static_assert((sizeof(TESModel) == 0x28), "layout");

// TESGrass: EXE_RTTI; class name and base from the image RTTI, 109 primary vftable slots
// sizeof TESGrass 0x78: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// Other RTTI bases (not declared here; their vftable pointers lie inside the members): .?AVTESModel@@
class TESGrass : public ::TESBoundObject, public ::TESModel
{
public:
	enum class GRASS_WATER_STATE : std::uint32_t
	{
		kAboveOnlyAtLeast = 0,
		kAboveOnlyAtMost = 1,
		kBelowOnlyAtLeast = 2,
		kBelowOnlyAtMost = 3,
		kBothAtLeast = 4,
		kBothAtMost = 5,
		kBothAtMostAbove = 6,
		kBothAtMostBelow = 7
	};

	// TESGrass::~TESGrass: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x270890, inherited name
	// community declaration: virtual ~BaseFormComponent();
	TESGrass();
	~TESGrass() override;  // 00
	// TESGrass::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x2704e0, inherited name
	// community declaration: virtual void InitializeData();
	void InitializeData() override;  // 04
	// TESGrass::Load: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6, target 0x270520, inherited name
	// community declaration: virtual bool Load(TESFile* a_mod);
	void Load() override;  // 06
	// TESGrass::InitItemImpl: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 19, target 0x270740, inherited name
	// community declaration: virtual void InitItemImpl();
	void InitItemImpl() override;  // 13
	// TESGrass::GetDensity: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 83, target 0x270900
	// community declaration: virtual std::uint8_t GetDensity() const;
	virtual std::uint8_t GetDensity() const;  // 53
	// TESGrass::SetDensity: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 84, target 0x2703d0
	// community declaration: virtual bool SetDensity(std::uint8_t a_density);
	virtual void SetDensity();  // 54
	// TESGrass::GetMinSlopeDegrees: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 85, target 0x270990
	// community declaration: virtual std::uint8_t GetMinSlopeDegrees() const;
	virtual std::uint8_t GetMinSlopeDegrees() const;  // 55
	// TESGrass::SetMinSlopeDegrees: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 86, target 0x2703f0
	// community declaration: virtual bool SetMinSlopeDegrees(std::uint8_t a_minSlope);
	virtual void SetMinSlopeDegrees();  // 56
	// TESGrass::GetMaxSlopeDegrees: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 87, target 0x270960
	// community declaration: virtual std::uint8_t GetMaxSlopeDegrees() const;
	virtual std::uint8_t GetMaxSlopeDegrees() const;  // 57
	// TESGrass::SetMaxSlopeDegrees: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 88, target 0x270410
	// community declaration: virtual bool SetMaxSlopeDegrees(std::uint8_t a_maxSlope);
	virtual void SetMaxSlopeDegrees();  // 58
	// TESGrass::GetMinSlope: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 89, target 0x270970
	// community declaration: virtual float GetMinSlope() const;
	virtual void GetMinSlope();  // 59
	// TESGrass::GetMaxSlope: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 90, target 0x270940
	// community declaration: virtual float GetMaxSlope() const;
	virtual void GetMaxSlope();  // 5A
	// TESGrass::GetDistanceFromWaterLevel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 91, target 0x270910
	// community declaration: virtual std::uint16_t GetDistanceFromWaterLevel() const;
	virtual std::uint16_t GetDistanceFromWaterLevel() const;  // 5B
	// TESGrass::SetDistanceFromWaterLevel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 92, target 0x2709f0
	// community declaration: virtual void SetDistanceFromWaterLevel(std::uint16_t a_unitsFromWater);
	virtual void SetDistanceFromWaterLevel();  // 5C
	// TESGrass::GetUnderwaterState: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 93, target 0x2709b0
	// community declaration: virtual GRASS_WATER_STATE GetUnderwaterState() const;
	virtual GRASS_WATER_STATE GetUnderwaterState() const;  // 5D
	// TESGrass::SetUnderwaterState: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 94, target 0x270a30
	// community declaration: virtual void SetUnderwaterState(GRASS_WATER_STATE a_waterState);
	virtual void SetUnderwaterState(GRASS_WATER_STATE a_waterState);  // 5E
	// TESGrass::GetPositionRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 95, target 0x2709a0
	// community declaration: virtual float GetPositionRange() const;
	virtual void GetPositionRange();  // 5F
	// TESGrass::SetPositionRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 96, target 0x270430
	// community declaration: virtual bool SetPositionRange(float a_positionRange);
	virtual void SetPositionRange();  // 60
	// TESGrass::GetHeightRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 97, target 0x270930
	// community declaration: virtual float GetHeightRange() const;
	virtual void GetHeightRange();  // 61
	// TESGrass::SetHeightRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 98, target 0x270460
	// community declaration: virtual bool SetHeightRange(float a_heightRange);
	virtual void SetHeightRange();  // 62
	// TESGrass::GetColorRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 99, target 0x2708f0
	// community declaration: virtual float GetColorRange() const;
	virtual void GetColorRange();  // 63
	// TESGrass::SetColorRange: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 100, target 0x270490
	// community declaration: virtual bool SetColorRange(float a_colorRange);
	virtual void SetColorRange();  // 64
	// TESGrass::GetWavePeriod: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 101, target 0x2709e0
	// community declaration: virtual float GetWavePeriod() const;
	virtual void GetWavePeriod();  // 65
	// TESGrass::SetWavePeriod: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 102, target 0x2704c0
	// community declaration: virtual bool SetWavePeriod(float a_wavePeriod);
	virtual void SetWavePeriod();  // 66
	// TESGrass::GetVertexLighting: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 103, target 0x2709d0
	// community declaration: virtual bool GetVertexLighting() const;
	virtual void GetVertexLighting();  // 67
	// TESGrass::SetVertexLighting: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 104, target 0x270a70
	// community declaration: virtual void SetVertexLighting(bool a_set);
	virtual void SetVertexLighting();  // 68
	// TESGrass::GetUniformScaling: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 105, target 0x2709c0
	// community declaration: virtual bool GetUniformScaling() const;
	virtual void GetUniformScaling();  // 69
	// TESGrass::SetUniformScaling: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 106, target 0x270a40
	// community declaration: virtual void SetUniformScaling(bool a_set);
	virtual void SetUniformScaling();  // 6A
	// TESGrass::GetFitToSlope: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 107, target 0x270920
	// community declaration: virtual bool GetFitToSlope() const;
	virtual void GetFitToSlope();  // 6B
	// TESGrass::SetFitToSlope: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 108, target 0x270a00
	// community declaration: virtual void SetFitToSlope(bool a_set);
	virtual void SetFitToSlope();  // 6C

	// GRASS_DATA: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); members used here only, offsets within DATA as in NG
	struct GRASS_DATA
	{
		std::int8_t   density;                 // 00
		std::int8_t   minSlopeDegrees;         // 01
		std::int8_t   maxSlopeDegrees;         // 02
		std::uint8_t  pad03;                   // 03
		std::uint16_t distanceFromWaterLevel;  // 04
		std::uint16_t pad06;                   // 06
		GRASS_WATER_STATE underwater;          // 08
		// unk0C: GUESS(low); NG names positionRange, heightRange, colorRange, wavePeriod, flags are not needed here
		std::uint8_t  unk0C[0x20 - 0x0C];      // 0C
	};
	static_assert((sizeof(GRASS_DATA) == 0x20), "layout");

	// data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; at 0x58 (density, slopes, distance, underwater)
	GRASS_DATA data;  // 58
};
static_assert((sizeof(TESGrass) == 0x78), "layout");
