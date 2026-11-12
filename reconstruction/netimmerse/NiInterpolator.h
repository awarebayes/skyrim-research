// NiInterpolator declaration for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT) include/RE/N/NiInterpolator.h,
// include/RE/N/NiObject.h and include/RE/N/NiRefObject.h. No body here is adapted from a
// community source; the only inline bodies are single returns or stores forced by the image.
// NiRefObject and NiObject are stand-ins declared in this header (not the shared NiObject.h):
// the target inlines the NiRefObject destructor into NiInterpolator's deleting destructor, so
// NiRefObject's destructor must be an inline body here. Vtable slot order comes from the image
// RTTI and vftable; sizeof(NiInterpolator) == 0x18 from the operator delete size argument.
// The name Clone is taken from powerof3/CommonLibSSE 654e55f (GPL-3.0) include/RE/N/NiObject.h;
// because of that one name this file states GPL-3.0 as its licence. It does not reproduce the
// GPL-3.0 text.
// NiInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once

#include <intrin.h>
#include <cstddef>
#include <cstdint>

class NiStream;
class NiCloningProcess;
class NiObjectGroup;
class NiAVObjectPalette;
class NiRTTI;
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
class NiControllerManager;

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
// _refCount, _pad0C, DeleteThis: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRefObject
{
public:
	// NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); inlined into the derived constructor
	// hot path: the engine bumps the shared object counter atomically on every construction
	NiRefObject() { _InterlockedIncrement(&ms_totalObjects); }
	// ~NiRefObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); inline here because the image inlines it
	// hot path: the engine drops the shared object counter atomically on every destruction
	virtual ~NiRefObject() { _InterlockedDecrement(&ms_totalObjects); }  // 00
	virtual void DeleteThis();  // 01

	static volatile long ms_totalObjects;

	std::uint32_t _refCount{ 0 };  // 08
	std::uint32_t _pad0C;          // 0C
};
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");

// NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// GetRTTI, AsNode, AsSwitchNode, AsFadeNode, AsMultiBoundNode, AsGeometry, AsTriStrips, AsTriShape, AsSegmentedTriShape, AsSubIndexTriShape, AsDynamicTriShape, AsNiGeometry, AsNiTriBasedGeom, AsNiTriShape, AsParticlesGeom, AsLinesGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
// AsBhkNiCollisionObject, AsBhkBlendCollisionObject, AsBhkAttachmentCollisionObject, AsBhkRigidBody, AsBhkLimitedHingeConstraint, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
// PostLinkObject, StreamCanSkip, GetStreamableRTTI, GetBlockAllocationSize, GetGroup, SetGroup, AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiObject virtuals in NG's slot order
class NiObject : public NiRefObject
{
public:
	NiObject() {}
	~NiObject() override {}  // 00
	virtual const NiRTTI*   GetRTTI() const;  // 02
	virtual NiNode*         AsNode();  // 03
	virtual NiSwitchNode*   AsSwitchNode();  // 04
	virtual BSFadeNode*     AsFadeNode();  // 05
	virtual BSMultiBoundNode* AsMultiBoundNode();  // 06
	virtual BSGeometry*     AsGeometry();  // 07
	virtual NiTriStrips*    AsTriStrips();  // 08
	virtual BSTriShape*     AsTriShape();  // 09
	virtual BSSegmentedTriShape* AsSegmentedTriShape();  // 0A
	virtual BSSubIndexTriShape* AsSubIndexTriShape();  // 0B
	virtual BSDynamicTriShape* AsDynamicTriShape();  // 0C
	virtual NiGeometry*     AsNiGeometry();  // 0D
	virtual NiTriBasedGeom* AsNiTriBasedGeom();  // 0E
	virtual NiTriShape*     AsNiTriShape();  // 0F
	virtual NiParticles*    AsParticlesGeom();  // 10
	virtual BSLines*        AsLinesGeom();  // 11
	virtual bhkNiCollisionObject* AsBhkNiCollisionObject();  // 12
	virtual bhkBlendCollisionObject* AsBhkBlendCollisionObject();  // 13
	virtual bhkAttachmentCollisionObject* AsBhkAttachmentCollisionObject();  // 14
	virtual bhkRigidBody*   AsBhkRigidBody();  // 15
	virtual bhkLimitedHingeConstraint* AsBhkLimitedHingeConstraint();  // 16
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
};
static_assert(sizeof(NiObject) == 0x10, "NiObject size");

// NiRTTI_NiInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's RTTI offset table name; declared here as a data object
extern NiRTTI NiRTTI_NiInterpolator;

// NiInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// ResolveDependencies, GetActiveTimeRange, GetSequenceInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Update1, Update2, Update3, Update4, Update5, Update6, IsBoolValueSupported, IsFloatValueSupported, IsQuaternionValueSupported, IsPoint3ValueSupported, IsColorAValueSupported, IsTransformValueSupported, Collapse, GuaranteeTimeRange, SetUpDependencies, AlwaysUpdate, AsNiBoolInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot names and order from the skeleton
// unk10: GUESS(low); members not recovered, sized so the static_assert holds
// Clone: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) OBSERVED; po3 declares NiObject::Clone, here a non-virtual member returning NiInterpolator* for the image function GetSequenceInterpolator calls. This file therefore states GPL-3.0 for that name
class NiInterpolator : public NiObject
{
public:
	NiInterpolator();
	~NiInterpolator() override;  // 00
	const NiRTTI* GetRTTI() const override;  // 02
	bool          RegisterStreamables(NiStream& a_stream) override;  // 1A
	virtual void  Update1();  // 25
	virtual void  Update2();  // 26
	virtual void  Update3();  // 27
	virtual void  Update4();  // 28
	virtual void  Update5();  // 29
	virtual void  Update6();  // 2A
	virtual void  IsBoolValueSupported();  // 2B
	virtual void  IsFloatValueSupported();  // 2C
	virtual void  IsQuaternionValueSupported();  // 2D
	virtual void  IsPoint3ValueSupported();  // 2E
	virtual void  IsColorAValueSupported();  // 2F
	virtual void  IsTransformValueSupported();  // 30
	virtual void  Collapse();  // 31
	virtual void  GetActiveTimeRange(float& a_beginKeyTime, float& a_endKeyTime) const;  // 32
	virtual void  GuaranteeTimeRange();  // 33
	virtual NiInterpolator* GetSequenceInterpolator(float a_startTime, float a_endTime);  // 34
	virtual bool  ResolveDependencies(NiAVObjectPalette* a_palette);  // 35
	virtual void  SetUpDependencies();  // 36
	virtual void  AlwaysUpdate();  // 37
	virtual void  AsNiBoolInterpolator();  // 38

	NiInterpolator* Clone();

	std::uint8_t unk10[0x8];  // 10
};
static_assert(sizeof(NiInterpolator) == 0x18, "NiInterpolator size");
