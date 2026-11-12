// NiObject type declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT) include/RE/N/NiObject.h,
// include/RE/N/NiRefObject.h, include/RE/N/NiCloningProcess.h and powerof3/CommonLibSSE 654e55f
// (GPL-3.0) include/RE/N/NiObject.h for Clone; this file therefore carries the GPL-3.0 notice of
// that source for the name Clone only. No community code is copied.
// Vtable slot order and sizeof(NiObject) == 0x10 come from the image RTTI and vftable.
// NiObject, NiRefObject, NiCloningProcess: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI; each declaration below carries its own label
#pragma once

#include <intrin.h>
#include <cstdint>

class NiCloningProcess;
class NiObject;
class NiControllerManager;
class NiObjectGroup;
class NiStream;
class NiNode;
class NiSwitchNode;
class BSFadeNode;
class BSMultiBoundNode;
class BSGeometry;
class NiTriStrips;
class BSTriShape;
class BSSegmentedTriShape;
class BSSubIndexTriShape;
class BSDynamicTriShape;
class NiGeometry;
class NiTriBasedGeom;
class NiTriShape;
class NiParticles;
class BSLines;
class bhkNiCollisionObject;
class bhkBlendCollisionObject;
class bhkAttachmentCollisionObject;
class bhkRigidBody;
class bhkLimitedHingeConstraint;

// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; only the name pointer is
// declared, at offset 0 (IsEqual reads a byte string through the first member).
// name: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRTTI
{
public:
	const char* name;  // 00
};

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// _refCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares it volatile, which makes this recipe order the constructor's stores differently from the image, so it is declared without volatile here
// _pad0C, DeleteThis: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
class NiRefObject
{
public:
	// NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); inlined into the NiObject constructor
	// hot path: the engine bumps the shared object counter atomically on every construction
	NiRefObject() { _InterlockedIncrement(&ms_totalObjects); }
	virtual ~NiRefObject();  // 00
	virtual void DeleteThis();  // 01

	static volatile long ms_totalObjects;

	std::uint32_t          _refCount{ 0 };  // 08
	std::uint32_t          _pad0C;          // 0C
};
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");

// NiObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Clone: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) OBSERVED; po3 declares no parameter, this routine takes the cloning process
// GetRTTI, AsNode, AsSwitchNode, AsFadeNode, AsMultiBoundNode, AsGeometry, AsTriStrips, AsTriShape, AsSegmentedTriShape, AsSubIndexTriShape, AsDynamicTriShape, AsNiGeometry, AsNiTriBasedGeom, AsNiTriShape, AsParticlesGeom, AsLinesGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
// AsBhkNiCollisionObject, AsBhkBlendCollisionObject, AsBhkAttachmentCollisionObject, AsBhkRigidBody, AsBhkLimitedHingeConstraint, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
// PostLinkObject, StreamCanSkip, GetStreamableRTTI, GetBlockAllocationSize, GetGroup, SetGroup, AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
class NiObject : public NiRefObject
{
public:
	NiObject();
	~NiObject() override;  // 00
	virtual const NiRTTI*   GetRTTI() const;  // 02
	virtual NiNode*         AsNode() { return nullptr; }  // 03
	virtual NiSwitchNode*   AsSwitchNode() { return nullptr; }  // 04
	virtual BSFadeNode*     AsFadeNode() { return nullptr; }  // 05
	virtual BSMultiBoundNode* AsMultiBoundNode() { return nullptr; }  // 06
	virtual BSGeometry*     AsGeometry() { return nullptr; }  // 07
	virtual NiTriStrips*    AsTriStrips() { return nullptr; }  // 08
	virtual BSTriShape*     AsTriShape() { return nullptr; }  // 09
	virtual BSSegmentedTriShape* AsSegmentedTriShape() { return nullptr; }  // 0A
	virtual BSSubIndexTriShape* AsSubIndexTriShape() { return nullptr; }  // 0B
	virtual BSDynamicTriShape* AsDynamicTriShape() { return nullptr; }  // 0C
	virtual NiGeometry*     AsNiGeometry() { return nullptr; }  // 0D
	virtual NiTriBasedGeom* AsNiTriBasedGeom() { return nullptr; }  // 0E
	virtual NiTriShape*     AsNiTriShape() { return nullptr; }  // 0F
	virtual NiParticles*    AsParticlesGeom() { return nullptr; }  // 10
	virtual BSLines*        AsLinesGeom() { return nullptr; }  // 11
	virtual bhkNiCollisionObject* AsBhkNiCollisionObject() { return nullptr; }  // 12
	virtual bhkBlendCollisionObject* AsBhkBlendCollisionObject() { return nullptr; }  // 13
	virtual bhkAttachmentCollisionObject* AsBhkAttachmentCollisionObject() { return nullptr; }  // 14
	virtual bhkRigidBody*   AsBhkRigidBody() { return nullptr; }  // 15
	virtual bhkLimitedHingeConstraint* AsBhkLimitedHingeConstraint() { return nullptr; }  // 16
	virtual NiObject*       CreateClone(NiCloningProcess& a_cloning);  // 17
	virtual void            LoadBinary(NiStream& a_stream);  // 18
	virtual void            LinkObject(NiStream& a_stream);  // 19
	virtual bool            RegisterStreamables(NiStream& a_stream);  // 1A
	virtual void            SaveBinary(NiStream& a_stream);  // 1B
	virtual bool            IsEqual(NiObject* a_object);  // 1C
	virtual void            ProcessClone(NiCloningProcess& a_cloning);  // 1D
	virtual void            PostLinkObject(NiStream& a_stream);  // 1E
	virtual bool            StreamCanSkip();  // 1F
	virtual const NiRTTI*   GetStreamableRTTI() const;  // 20
	virtual std::uint32_t   GetBlockAllocationSize() const;  // 21
	virtual NiObjectGroup*  GetGroup() const;  // 22
	virtual void            SetGroup(NiObjectGroup* a_group);  // 23
	virtual NiControllerManager* AsNiControllerManager();  // 24

	NiObject* Clone(NiCloningProcess& a_cloning);
};
static_assert(sizeof(NiObject) == 0x10, "NiObject size");
