// Type declarations for the NiNode translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (community-headers, binary-analysis of the pinned image).
// Licence: the class chain and slot names derive from CharmedBaryon/CommonLibSSE-NG (MIT) and
// powerof3/CommonLibSSE (GPL-3.0, docs/authorizations.md); this header is GPL-3.0 as a result.
// Layout and slot order come from the image RTTI and vftables (tools/ghidra/class_skeleton.py);
// signatures are restored from the community declarations. Every class here is a stand-in that
// declares only what the unit needs; the vtable slot placeholders keep later slots in place.
// Array members: NiTArray holds the 16-bit capacity, filled index, size and growth at
// +0x10..+0x16, as the community NiTArray declares them.
// NiTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiTObjectArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiStream, NiBinaryStream, NiUpdateData, NiBound, NiTimeController, NiCullingProcess: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// _data, _capacity, _freeIdx, _size, _growthSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiTArray members at NG's offsets
// center, radius: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiBound members
// _writeFn, oStr, _absoluteCurrentPos: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// SetArraySize: GUESS; non-virtual array resize called by LinkObject, bound by hint to 0x2d6180
// radiusBits: GUESS; integer view of the radius, the image tests it as an integer against zero
// NiStream::ReadLinkIDCount, NiStream::ReadLinkID, NiStream::SkipLinkIDs: GUESS; stream helpers bound by hint
#pragma once

#include <cstdint>

class NiNode;
class NiAVObject;
class NiStream;
class NiTimeController;
class NiCullingProcess;
class NiUpdateData;
class NiCloningProcess;

// NiTArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout from the image, element type is a pointer in this unit
template <class T>
class NiTArray
{
public:
	virtual ~NiTArray();  // 00

	T*            _data;        // 08
	std::uint16_t _capacity;    // 10
	std::uint16_t _freeIdx;     // 12
	std::uint16_t _size;        // 14
	std::uint16_t _growthSize;  // 16
};

template <class T>
class NiTObjectArray : public NiTArray<T>
{
};

// SetArraySize: GUESS
void SetArraySize(NiTObjectArray<NiAVObject*>& a_array, std::uint32_t a_size);

// NiPoint3: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiPoint3
{
public:
	float x;  // 0
	float y;  // 4
	float z;  // 8
};

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value. The image tests
// node flags as a load, a shift by the bit index and a test of the low bit, which this recipe keeps
// only when the shift count reaches the test through an inlined call; a bit-field or mask test of
// the member folds to a test of memory or a bt.
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
	return ((a_flags >> a_bit) & 1) != 0;
}

// NiBound: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); centre and radius, the radius is read as an integer by the image
class NiBound
{
public:
	NiPoint3 center;  // 00
	union {
		float        radius;      // 0C
		std::int32_t radiusBits;  // 0C
	};
};

// NiRefObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 2 primary vftable slots
// sizeof NiRefObject 0x10: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class NiRefObject
{
public:
	// NiRefObject::~NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0x213be0
	// community declaration: virtual ~NiRefObject();
	virtual ~NiRefObject();  // 00
	// NiRefObject::DeleteThis: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0xeebf20
	// community declaration: virtual void DeleteThis();
	virtual void DeleteThis();  // 01

	// unk08: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk08[0x8];  // 08
};
static_assert(sizeof(NiRefObject) == 0x10, "layout");

// NiObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 37 primary vftable slots
// sizeof NiObject 0x10: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class NiObject : public ::NiRefObject
{
public:
	// NiObject::~NiObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0xedd080, inherited name
	// community declaration: virtual ~NiRefObject();
	~NiObject() override;  // 00
	// NiObject::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0x2a56f0
	// community declaration: [[nodiscard]] virtual const NiRTTI* GetRTTI() const;
	virtual void GetRTTI();  // 02
	// NiObject::AsNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x20bec0
	// community declaration: virtual NiNode* AsNode() { return nullptr; }
	virtual void AsNode();  // 03
	// NiObject::AsSwitchNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4, target 0x1b4d50
	// community declaration: virtual NiSwitchNode* AsSwitchNode() { return nullptr; }
	virtual void AsSwitchNode();  // 04
	// NiObject::AsFadeNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5, target 0x1b4ca0
	// community declaration: virtual BSFadeNode* AsFadeNode() { return nullptr; }
	virtual void AsFadeNode();  // 05
	// NiObject::AsMultiBoundNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6, target 0x1b4cd0
	// community declaration: virtual BSMultiBoundNode* AsMultiBoundNode() { return nullptr; }
	virtual void AsMultiBoundNode();  // 06
	// NiObject::AsGeometry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 7, target 0x1b4cb0
	// community declaration: virtual BSGeometry* AsGeometry() { return nullptr; }
	virtual void AsGeometry();  // 07
	// NiObject::AsTriStrips: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 8, target 0x1b4d70
	// community declaration: virtual NiTriStrips* AsTriStrips() { return nullptr; }
	virtual void AsTriStrips();  // 08
	// NiObject::AsTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 9, target 0x1b4d60
	// community declaration: virtual BSTriShape* AsTriShape() { return nullptr; }
	virtual void AsTriShape();  // 09
	// NiObject::AsSegmentedTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 10, target 0x1b4d30
	// community declaration: virtual BSSegmentedTriShape* AsSegmentedTriShape() { return nullptr; }
	virtual void AsSegmentedTriShape();  // 0A
	// NiObject::AsSubIndexTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 11, target 0x1b4d40
	// community declaration: virtual BSSubIndexTriShape* AsSubIndexTriShape() { return nullptr; }
	virtual void AsSubIndexTriShape();  // 0B
	// NiObject::AsDynamicTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 12, target 0x1b4c90
	// community declaration: virtual BSDynamicTriShape* AsDynamicTriShape() { return nullptr; }
	virtual void AsDynamicTriShape();  // 0C
	// NiObject::AsNiGeometry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 13, target 0x1b4ce0
	// community declaration: virtual NiGeometry* AsNiGeometry() { return nullptr; }
	virtual void AsNiGeometry();  // 0D
	// NiObject::AsNiTriBasedGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 14, target 0x1b4cf0
	// community declaration: virtual NiTriBasedGeom* AsNiTriBasedGeom() { return nullptr; }
	virtual void AsNiTriBasedGeom();  // 0E
	// NiObject::AsNiTriShape: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 15, target 0x1b4d00
	// community declaration: virtual NiTriShape* AsNiTriShape() { return nullptr; }
	virtual void AsNiTriShape();  // 0F
	// NiObject::AsParticlesGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 16, target 0x1b4d20
	// community declaration: virtual NiParticles* AsParticlesGeom() { return nullptr; }
	virtual void AsParticlesGeom();  // 10
	// NiObject::AsLinesGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 17, target 0x1b4cc0
	// community declaration: virtual BSLines* AsLinesGeom() { return nullptr; }
	virtual void AsLinesGeom();  // 11
	// NiObject::AsBhkNiCollisionObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 18, target 0x1b4c70
	// community declaration: virtual bhkNiCollisionObject* AsBhkNiCollisionObject() { return nullptr; }
	virtual void AsBhkNiCollisionObject();  // 12
	// NiObject::AsBhkBlendCollisionObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 19, target 0x1b4c50
	// community declaration: virtual bhkBlendCollisionObject* AsBhkBlendCollisionObject() { return nullptr; }
	virtual void AsBhkBlendCollisionObject();  // 13
	// NiObject::AsBhkAttachmentCollisionObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 20, target 0x1b4c40
	// community declaration: virtual bhkAttachmentCollisionObject* AsBhkAttachmentCollisionObject() { return nullptr; }
	virtual void AsBhkAttachmentCollisionObject();  // 14
	// NiObject::AsBhkRigidBody: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 21, target 0x1b4c80
	// community declaration: virtual bhkRigidBody* AsBhkRigidBody() { return nullptr; }
	virtual void AsBhkRigidBody();  // 15
	// NiObject::AsBhkLimitedHingeConstraint: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 22, target 0x1b4c60
	// community declaration: virtual bhkLimitedHingeConstraint* AsBhkLimitedHingeConstraint() { return nullptr; }
	virtual void AsBhkLimitedHingeConstraint();  // 16
	// NiObject::CreateClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 23, target 0xedc740
	// community declaration: virtual NiObject* CreateClone([[maybe_unused]] NiCloningProcess& a_cloning) { return this; }
	virtual void CreateClone();  // 17
	// NiObject::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0xedc790
	// community declaration: virtual void LoadBinary([[maybe_unused]] NiStream& a_stream) { return; }
	virtual void LoadBinary(NiStream& a_stream);  // 18
	// NiObject::LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0xedc7a0
	// community declaration: virtual void LinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	virtual void LinkObject(NiStream& a_stream);  // 19
	// NiObject::RegisterStreamables: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0xedc7b0
	// community declaration: virtual bool RegisterStreamables(NiStream& a_stream);
	virtual bool RegisterStreamables(NiStream& a_stream);  // 1A
	// NiObject::SaveBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0xedc7d0
	// community declaration: virtual void SaveBinary([[maybe_unused]] NiStream& a_stream) { return; }
	virtual void SaveBinary(NiStream& a_stream);  // 1B
	// NiObject::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0xedc7e0
	// community declaration: virtual bool IsEqual(NiObject* a_object);
	virtual bool IsEqual(NiObject* a_object);  // 1C
	// NiObject::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0xedca00
	// community declaration: virtual void ProcessClone(NiCloningProcess& a_cloning);
	virtual void ProcessClone();  // 1D
	// NiObject::PostLinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 30, target 0xedcb50
	// community declaration: virtual void PostLinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	virtual void PostLinkObject();  // 1E
	// NiObject::StreamCanSkip: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 31, target 0xedcb60
	// community declaration: virtual bool StreamCanSkip() { return false; }
	virtual void StreamCanSkip();  // 1F
	// NiObject::GetStreamableRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 32, target 0xedcb70
	// community declaration: [[nodiscard]] virtual const NiRTTI* GetStreamableRTTI() const { return GetRTTI(); }
	virtual void GetStreamableRTTI();  // 20
	// NiObject::GetBlockAllocationSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 33, target 0xedcb80
	// community declaration: [[nodiscard]] virtual std::uint32_t GetBlockAllocationSize() const { return 0; }
	virtual void GetBlockAllocationSize();  // 21
	// NiObject::GetGroup: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 34, target 0xedcb90
	// community declaration: [[nodiscard]] virtual NiObjectGroup* GetGroup() const { return nullptr; }
	virtual void GetGroup();  // 22
	// NiObject::SetGroup: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 35, target 0xedcba0
	// community declaration: virtual void SetGroup([[maybe_unused]] NiObjectGroup* a_group) { return; }
	virtual void SetGroup();  // 23
	// NiObject::AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 36, target 0xedcbb0
	// community declaration: virtual NiControllerManager* AsNiControllerManager() { return nullptr; }
	virtual void AsNiControllerManager();  // 24
};
static_assert(sizeof(NiObject) == 0x10, "layout");

// NiObjectNET: STANDIN EXE_RTTI; class name and base from the image RTTI, 37 primary vftable slots
// sizeof NiObjectNET 0x30: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class NiObjectNET : public ::NiObject
{
public:
	// NiObjectNET::~NiObjectNET: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0xeebba0, inherited name
	// community declaration: virtual ~NiRefObject();
	~NiObjectNET() override;  // 00
	// NiObjectNET::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0xeebcd0, inherited name
	// community declaration: [[nodiscard]] virtual const NiRTTI* GetRTTI() const;
	void GetRTTI() override;  // 02
	// NiObjectNET::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0xeea6c0, inherited name
	// community declaration: virtual void LoadBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void LoadBinary(NiStream& a_stream) override;  // 18
	// NiObjectNET::LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0xeea710, inherited name
	// community declaration: virtual void LinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	void LinkObject(NiStream& a_stream) override;  // 19
	// NiObjectNET::RegisterStreamables: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0xeea7b0, inherited name
	// community declaration: virtual bool RegisterStreamables(NiStream& a_stream);
	bool RegisterStreamables(NiStream& a_stream) override;  // 1A
	// NiObjectNET::SaveBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0xeea880, inherited name
	// community declaration: virtual void SaveBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void SaveBinary(NiStream& a_stream) override;  // 1B
	// NiObjectNET::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0xeea9a0, inherited name
	// community declaration: virtual bool IsEqual(NiObject* a_object);
	bool IsEqual(NiObject* a_object) override;  // 1C
	// NiObjectNET::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0xeeb8c0, inherited name
	// community declaration: virtual void ProcessClone(NiCloningProcess& a_cloning);
	void ProcessClone() override;  // 1D
	// NiObjectNET::PostLinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 30, target 0xeeb800, inherited name
	// community declaration: virtual void PostLinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	void PostLinkObject() override;  // 1E

	// unk10: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk10[0x8];  // 10
	// controllers: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); head of the controller list, NiPointer there
	NiTimeController* controllers;  // 18
	// unk20: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk20[0x10];  // 20
};
static_assert(sizeof(NiObjectNET) == 0x30, "layout");

// NiAVObject: STANDIN EXE_RTTI; class name and base from the image RTTI, 53 primary vftable slots
// sizeof NiAVObject 0x110: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class NiAVObject : public ::NiObjectNET
{
public:
	// NiAVObject::~NiAVObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0xee1250, inherited name
	// community declaration: virtual ~NiRefObject();
	~NiAVObject() override;  // 00
	// NiAVObject::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0xee1310, inherited name
	// community declaration: [[nodiscard]] virtual const NiRTTI* GetRTTI() const;
	void GetRTTI() override;  // 02
	// NiAVObject::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0xee05a0, inherited name
	// community declaration: virtual void LoadBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void LoadBinary(NiStream& a_stream) override;  // 18
	// NiAVObject::LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0xee0680, inherited name
	// community declaration: virtual void LinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	void LinkObject(NiStream& a_stream) override;  // 19
	// NiAVObject::RegisterStreamables: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0xee0700, inherited name
	// community declaration: virtual bool RegisterStreamables(NiStream& a_stream);
	bool RegisterStreamables(NiStream& a_stream) override;  // 1A
	// NiAVObject::SaveBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0xee0750, inherited name
	// community declaration: virtual void SaveBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void SaveBinary(NiStream& a_stream) override;  // 1B
	// NiAVObject::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0xee0810, inherited name
	// community declaration: virtual bool IsEqual(NiObject* a_object);
	bool IsEqual(NiObject* a_object) override;  // 1C
	// NiAVObject::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0xee0f70, inherited name
	// community declaration: virtual void ProcessClone(NiCloningProcess& a_cloning);
	void ProcessClone() override;  // 1D
	// NiAVObject::UpdateControllers: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 37, target 0xee09b0
	// community declaration: virtual void UpdateControllers(NiUpdateData& a_data);
	virtual void UpdateControllers();  // 25
	// NiAVObject::PerformOp: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 38, target 0xee0a00
	// community declaration: virtual void PerformOp(PerformOpFunc& a_func);
	virtual void PerformOp();  // 26
	// NiAVObject::AttachProperty: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 39, target 0xee1300
	// community declaration: virtual void AttachProperty(NiAlphaProperty* a_property);
	virtual void AttachProperty();  // 27
	// NiAVObject::SetMaterialNeedsUpdate: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 40, target 0xee0a20
	// community declaration: virtual void SetMaterialNeedsUpdate(bool a_needsUpdate);
	virtual void SetMaterialNeedsUpdate();  // 28
	// NiAVObject::SetDefaultMaterialNeedsUpdateFlag: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 41, target 0xee0a30
	// community declaration: virtual void SetDefaultMaterialNeedsUpdateFlag(bool a_flag);
	virtual void SetDefaultMaterialNeedsUpdateFlag();  // 29
	// NiAVObject::GetObjectByName: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 42, target 0xee0a40
	// community declaration: virtual NiAVObject* GetObjectByName(const BSFixedString& a_name);
	virtual void GetObjectByName();  // 2A
	// NiAVObject::SetSelectiveUpdateFlags: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 43, target 0xee0a60
	// community declaration: virtual void SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid);
	virtual void SetSelectiveUpdateFlags();  // 2B
	// NiAVObject::UpdateDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 44, target 0xee0b30
	// community declaration: virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // 2C
	// NiAVObject::UpdateSelectedDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 45, target 0xee0bb0
	// community declaration: virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	virtual void UpdateSelectedDownwardPass();  // 2D
	// NiAVObject::UpdateRigidDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 46, target 0xee0c90
	// community declaration: virtual void UpdateRigidDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	virtual void UpdateRigidDownwardPass();  // 2E
	// NiAVObject::UpdateWorldBound: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 47, target 0xee1320
	// community declaration: virtual void UpdateWorldBound();
	virtual void UpdateWorldBound();  // 2F
	// NiAVObject::UpdateWorldData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 48, target 0xeebf40
	// community declaration: virtual void UpdateWorldData(NiUpdateData* a_data);
	virtual void UpdateWorldData(NiUpdateData* a_data);  // 30
	// NiAVObject::UpdateTransformAndBounds: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 49, target 0xee0e50
	// community declaration: virtual void UpdateTransformAndBounds(NiUpdateData& a_data);
	virtual void UpdateTransformAndBounds();  // 31
	// NiAVObject::PreAttachUpdate: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 50, target 0xee0e90
	// community declaration: virtual void PreAttachUpdate(NiNode* a_parent, NiUpdateData& a_data);
	virtual void PreAttachUpdate();  // 32
	// NiAVObject::PostAttachUpdate: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 51, target 0xee0ed0
	// community declaration: virtual void PostAttachUpdate();
	virtual void PostAttachUpdate();  // 33
	// NiAVObject::OnVisible: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 52, target 0xee0f60
	// community declaration: virtual void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);
	virtual void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);  // 34

	// NiAVObject::Cull: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); non-virtual per-child visit called by NiNode::OnVisible, bound by hint to 0xee0f30
	void Cull(NiCullingProcess* a_culler, std::int32_t a_alphaGroupIndex);

	// parent, parentIndex: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	NiNode*       parent;       // 30
	std::uint32_t parentIndex;  // 38
	// unk3C: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk3C[0xA8];  // 3C
	// worldBound, flags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	// kHidden, kAlwaysDraw, kFixedBound, kNoDismemberValidity: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's NiAVObject::Flag enumerators at the same bits, declared here as one-bit fields
	// unk1, unk12, unk14, unk22: GUESS(low); placeholders for bits no compared function uses; NG names them in NiAVObject::Flag
	NiBound       worldBound;  // E4
	struct {
		std::uint32_t kHidden : 1;               // bit 0
		std::uint32_t unk1 : 10;                 // bits 1 to 10
		std::uint32_t kAlwaysDraw : 1;           // bit 11
		std::uint32_t unk12 : 1;                 // bit 12
		std::uint32_t kFixedBound : 1;           // bit 13
		std::uint32_t unk14 : 7;                 // bits 14 to 20
		std::uint32_t kNoDismemberValidity : 1;  // bit 21
		std::uint32_t unk22 : 10;                // bits 22 to 31
	} flags;  // F4
	// kAlwaysDrawBit: GUESS; bit index of NG's kAlwaysDraw (1 << 11), for TestBit
	static constexpr std::uint32_t kAlwaysDrawBit = 11;
	// FlagWord: GUESS(low); the flag bits above as one word, for TestBit.
	std::uint32_t FlagWord() const { return *reinterpret_cast<const std::uint32_t*>(&flags); }
	// unkF8: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unkF8[0x18];  // F8
};
static_assert(sizeof(NiAVObject) == 0x110, "layout");

// NiNode: EXE_RTTI; class name and base from the image RTTI, 62 primary vftable slots
// sizeof NiNode 0x128: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class NiNode : public ::NiAVObject
{
public:
	// NiNode::~NiNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0, target 0xee3330, inherited name
	// community declaration: virtual ~NiRefObject();
	~NiNode() override;  // 00
	// NiNode::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2, target 0xee3530, inherited name
	// community declaration: [[nodiscard]] virtual const NiRTTI* GetRTTI() const;
	void GetRTTI() override;  // 02
	// NiNode::AsNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3, target 0x1b4d10, inherited name
	// community declaration: virtual NiNode* AsNode() { return nullptr; }
	void AsNode() override;  // 03
	// NiNode::CreateClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 23, target 0xee1330, inherited name
	// community declaration: virtual NiObject* CreateClone([[maybe_unused]] NiCloningProcess& a_cloning) { return this; }
	void CreateClone() override;  // 17
	// NiNode::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 24, target 0xee1560, inherited name
	// community declaration: virtual void LoadBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void LoadBinary(NiStream& a_stream) override;  // 18
	// NiNode::LinkObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 25, target 0xee15a0, inherited name
	// community declaration: virtual void LinkObject([[maybe_unused]] NiStream& a_stream) { return; }
	void LinkObject(NiStream& a_stream) override;  // 19
	// NiNode::RegisterStreamables: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 26, target 0xee1650, inherited name
	// community declaration: virtual bool RegisterStreamables(NiStream& a_stream);
	bool RegisterStreamables(NiStream& a_stream) override;  // 1A
	// NiNode::SaveBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 27, target 0xee16e0, inherited name
	// community declaration: virtual void SaveBinary([[maybe_unused]] NiStream& a_stream) { return; }
	void SaveBinary(NiStream& a_stream) override;  // 1B
	// NiNode::IsEqual: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 28, target 0xee17b0, inherited name
	// community declaration: virtual bool IsEqual(NiObject* a_object);
	bool IsEqual(NiObject* a_object) override;  // 1C
	// NiNode::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 29, target 0xee2f60, inherited name
	// community declaration: virtual void ProcessClone(NiCloningProcess& a_cloning);
	void ProcessClone() override;  // 1D
	// NiNode::UpdateControllers: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 37, target 0xee2420, inherited name
	// community declaration: virtual void UpdateControllers(NiUpdateData& a_data);
	void UpdateControllers() override;  // 25
	// NiNode::PerformOp: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 38, target 0xee2310, inherited name
	// community declaration: virtual void PerformOp(PerformOpFunc& a_func);
	void PerformOp() override;  // 26
	// NiNode::AttachProperty: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 39, target 0xee3010, inherited name
	// community declaration: virtual void AttachProperty(NiAlphaProperty* a_property);
	void AttachProperty() override;  // 27
	// NiNode::GetObjectByName: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 42, target 0xee23a0, inherited name
	// community declaration: virtual NiAVObject* GetObjectByName(const BSFixedString& a_name);
	void GetObjectByName() override;  // 2A
	// NiNode::SetSelectiveUpdateFlags: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 43, target 0xee2e30, inherited name
	// community declaration: virtual void SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid);
	void SetSelectiveUpdateFlags() override;  // 2B
	// NiNode::UpdateDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 44, target 0xee24d0, inherited name
	// community declaration: virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2) override;  // 2C
	// NiNode::UpdateSelectedDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 45, target 0xee2680, inherited name
	// community declaration: virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	void UpdateSelectedDownwardPass() override;  // 2D
	// NiNode::UpdateRigidDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 46, target 0xee2a40, inherited name
	// community declaration: virtual void UpdateRigidDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	void UpdateRigidDownwardPass() override;  // 2E
	// NiNode::UpdateWorldBound: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 47, target 0xee2920, inherited name
	// community declaration: virtual void UpdateWorldBound();
	void UpdateWorldBound() override;  // 2F
	// NiNode::UpdateTransformAndBounds: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 49, target 0xee2b70, inherited name
	// community declaration: virtual void UpdateTransformAndBounds(NiUpdateData& a_data);
	void UpdateTransformAndBounds() override;  // 31
	// NiNode::OnVisible: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 52, target 0xee2cc0, inherited name
	// community declaration: virtual void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);
	void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex) override;  // 34
	// NiNode::AttachChild: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 53, target 0xee1b00
	// community declaration: virtual void AttachChild(NiAVObject* a_child, bool a_firstAvail = false);
	virtual void AttachChild();  // 35
	// NiNode::InsertChildAt: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 54, target 0xee1c70
	// community declaration: virtual void InsertChildAt(std::uint32_t a_idx, NiAVObject* a_child);
	virtual void InsertChildAt();  // 36
	// NiNode::DetachChild1: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 55, target 0xee1d60
	// community declaration: virtual void DetachChild1(NiAVObject* a_child, NiPointer<NiAVObject>& a_childOut);
	virtual void DetachChild1();  // 37
	// NiNode::DetachChild2: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 56, target 0xee1d10
	// community declaration: virtual void DetachChild2(NiAVObject* a_child);
	virtual void DetachChild2();  // 38
	// NiNode::DetachChildAt1: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 57, target 0xee1f20
	// community declaration: virtual void DetachChildAt1(std::uint32_t a_idx, NiPointer<NiAVObject>& a_childOut);
	virtual void DetachChildAt1();  // 39
	// NiNode::DetachChildAt2: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 58, target 0xee1ed0
	// community declaration: virtual void DetachChildAt2(std::uint32_t a_idx);
	virtual void DetachChildAt2();  // 3A
	// NiNode::SetAt1: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 59, target 0xee2150
	// community declaration: virtual void SetAt1(std::uint32_t a_idx, NiAVObject* a_child, NiPointer<NiAVObject>& a_childOut);
	virtual void SetAt1();  // 3B
	// NiNode::SetAt2: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 60, target 0xee2100
	// community declaration: virtual void SetAt2(std::uint32_t a_idx, NiAVObject* a_child);
	virtual void SetAt2(std::uint32_t a_idx, NiAVObject* a_child);  // 3C
	// NiNode::UpdateUpwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); slot 61, target 0xee28e0
	// community declaration: virtual void UpdateUpwardPass(NiUpdateData& a_data);
	virtual void UpdateUpwardPass();  // 3D

	// children: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiPointer elements, plain pointers here
	NiTObjectArray<NiAVObject*> children;  // 110
};
static_assert(sizeof(NiNode) == 0x128, "layout");

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); write path only
class NiBinaryStream
{
public:
	using WriteFn = std::uint32_t(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

	template <class CharT>
	bool write(const CharT* a_str, std::uint32_t a_count)
	{
		std::uint32_t size = sizeof(CharT);
		std::uint32_t toWrite = a_count * size;
		std::uint32_t bytesWritten = binary_write(a_str, toWrite, &size);
		return bytesWritten == toWrite;
	}

	std::uint32_t binary_write(const void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		std::uint32_t written = _writeFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += written;
		return written;
	}

	virtual ~NiBinaryStream();  // 00

	std::uint32_t _absoluteCurrentPos;  // 08
	std::uint32_t _pad0C;               // 0C
	void*         _readFn;              // 10
	WriteFn*      _writeFn;             // 18
};

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 0 to 0xC only
class NiStream
{
public:
	virtual ~NiStream();  // 00
	virtual void Unk_01();  // 01
	virtual void Unk_02();  // 02
	virtual void Unk_03();  // 03
	virtual void Unk_04();  // 04
	virtual void Unk_05();  // 05
	virtual void Unk_06();  // 06
	virtual void Unk_07();  // 07
	virtual void Unk_08();  // 08
	virtual void Unk_09();  // 09
	virtual void Unk_0A();  // 0A
	virtual void Unk_0B();  // 0B
	virtual void SaveLinkID(const NiObject* a_object);  // 0C

	// NiStream::ReadLinkIDCount: GUESS; reads a count of link ids
	std::uint32_t ReadLinkIDCount();
	// NiStream::ReadLinkID: GUESS; reads one link id and resolves it to an object
	NiAVObject* ReadLinkID();
	// NiStream::SkipLinkIDs: GUESS; consumes the list headers of the base streamables
	void SkipLinkIDs();

	std::uint8_t    unk08[0x290];  // 08
	NiBinaryStream* iStr;          // 298
	NiBinaryStream* oStr;          // 2A0
};
