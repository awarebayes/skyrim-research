// NiExtraData type declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT) include/RE/N/NiExtraData.h and
// include/RE/N/NiStream.h. No body is adapted from community or FNV sources; the lone
// declarations are community ones. tools/check_origin.py reports none above its threshold.
// NiRefObject and NiObject are stand-ins here (the shared NiObject.h cannot inline their
// destructors); NiStream and BSFixedString are minimal
// stand-ins declared below (NG include/RE/N/NiStream.h, include/RE/B/BSFixedString.h).
// Vtable slot order and sizeof(NiExtraData) == 0x18 come from the image vftable and the size
// argument of operator delete in the deleting destructor.
// NiExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once

#include <intrin.h>
#include <cstdint>

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
class NiCloningProcess;
class NiObjectGroup;
class NiControllerManager;

class NiStream;

// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only returned by pointer
class NiRTTI;

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ~NiRefObject, DeleteThis, _refCount, _pad0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
// The destructor is defined inline here because the image inlines it into NiExtraData's
// deleting destructor (header-gap NiRefObject: the shared NiObject.h declares it out of line).
class NiRefObject
{
public:
	virtual ~NiRefObject()
	{
		// hot path: the engine drops the shared object counter atomically on every destruction
		_InterlockedDecrement(&ms_totalObjects);
	}
	virtual void DeleteThis();  // 01

	static volatile long ms_totalObjects;

	std::uint32_t _refCount{ 0 };  // 08
	std::uint32_t _pad0C;          // 0C
};

// NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Slots in NG's order, declared without bodies (only the order matters here); header-gap NiObject:
// the shared NiObject.h declares ~NiObject out of line, but the image inlines it.
// ~NiObject, GetRTTI, AsNode, AsSwitchNode, AsFadeNode, AsMultiBoundNode, AsGeometry, AsTriStrips, AsTriShape, AsSegmentedTriShape, AsSubIndexTriShape, AsDynamicTriShape, AsNiGeometry, AsNiTriBasedGeom, AsNiTriShape, AsParticlesGeom, AsLinesGeom, AsBhkNiCollisionObject, AsBhkBlendCollisionObject, AsBhkAttachmentCollisionObject, AsBhkRigidBody, AsBhkLimitedHingeConstraint, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone, PostLinkObject, StreamCanSkip, GetStreamableRTTI, GetBlockAllocationSize, GetGroup, SetGroup, AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiObject : public NiRefObject
{
public:
	~NiObject() override {}  // 00
	virtual const NiRTTI* GetRTTI() const;  // 02
	virtual NiNode* AsNode();  // 03
	virtual NiSwitchNode* AsSwitchNode();  // 04
	virtual BSFadeNode* AsFadeNode();  // 05
	virtual BSMultiBoundNode* AsMultiBoundNode();  // 06
	virtual BSGeometry* AsGeometry();  // 07
	virtual NiTriStrips* AsTriStrips();  // 08
	virtual BSTriShape* AsTriShape();  // 09
	virtual BSSegmentedTriShape* AsSegmentedTriShape();  // 0A
	virtual BSSubIndexTriShape* AsSubIndexTriShape();  // 0B
	virtual BSDynamicTriShape* AsDynamicTriShape();  // 0C
	virtual NiGeometry* AsNiGeometry();  // 0D
	virtual NiTriBasedGeom* AsNiTriBasedGeom();  // 0E
	virtual NiTriShape* AsNiTriShape();  // 0F
	virtual NiParticles* AsParticlesGeom();  // 10
	virtual BSLines* AsLinesGeom();  // 11
	virtual bhkNiCollisionObject* AsBhkNiCollisionObject();  // 12
	virtual bhkBlendCollisionObject* AsBhkBlendCollisionObject();  // 13
	virtual bhkAttachmentCollisionObject* AsBhkAttachmentCollisionObject();  // 14
	virtual bhkRigidBody* AsBhkRigidBody();  // 15
	virtual bhkLimitedHingeConstraint* AsBhkLimitedHingeConstraint();  // 16
	virtual NiObject* CreateClone(NiCloningProcess& a_cloning);  // 17
	virtual void LoadBinary(NiStream& a_stream);  // 18
	virtual void LinkObject(NiStream& a_stream);  // 19
	virtual bool RegisterStreamables(NiStream& a_stream);  // 1A
	virtual void SaveBinary(NiStream& a_stream);  // 1B
	virtual bool IsEqual(NiObject* a_object);  // 1C
	virtual void ProcessClone(NiCloningProcess& a_cloning);  // 1D
	virtual void PostLinkObject(NiStream& a_stream);  // 1E
	virtual bool StreamCanSkip();  // 1F
	virtual const NiRTTI* GetStreamableRTTI() const;  // 20
	virtual std::uint32_t GetBlockAllocationSize() const;  // 21
	virtual NiObjectGroup* GetGroup() const;  // 22
	virtual void SetGroup(NiObjectGroup* a_group);  // 23
	virtual NiControllerManager* AsNiControllerManager();  // 24
};
static_assert(sizeof(NiObject) == 0x10, "NiObject size");

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer to the pooled string
// _data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ~BSFixedString: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG inlines it as try_release, the image calls a routine, so it is declared out of line
class BSFixedString
{
public:
	~BSFixedString();

	const char* _data{ nullptr };  // 00
};

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the slots up to RegisterFixedString
// ~NiStream, Load1, Load2, Load3, Save1, Save2, Save3, Unk_07, RegisterFixedString: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot order as NG
// LoadFixedString: GUESS(low); non-virtual routine the image calls with the stream and a string slot
class NiStream
{
public:
	virtual ~NiStream();  // 00
	virtual bool Load1(void* a_stream);  // 01
	virtual bool Load2(char* a_buffer, std::uint64_t a_len);  // 02
	virtual bool Load3(const char* a_path);  // 03
	virtual bool Save1(void* a_stream);  // 04
	virtual bool Save2(char*& a_path, std::uint64_t& a_len);  // 05
	virtual bool Save3(const char* a_path);  // 06
	virtual void Unk_07();  // 07
	virtual bool RegisterFixedString(const BSFixedString& a_fixedString);  // 08

	void LoadFixedString(BSFixedString& a_string);
};

// NiExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// ~NiExtraData, GetRTTI, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, IsStreamable, IsCloneable, name: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot order as NG
class NiExtraData : public NiObject
{
public:
	NiExtraData();
	~NiExtraData() override;  // 00
	const NiRTTI* GetRTTI() const override;  // 02
	void LoadBinary(NiStream& a_stream) override;  // 18
	void LinkObject(NiStream& a_stream) override;  // 19
	bool RegisterStreamables(NiStream& a_stream) override;  // 1A
	void SaveBinary(NiStream& a_stream) override;  // 1B
	bool IsEqual(NiObject* a_object) override;  // 1C
	virtual bool IsStreamable() const;  // 25
	virtual bool IsCloneable() const;  // 26

	BSFixedString name;  // 10
};
static_assert(sizeof(NiExtraData) == 0x18, "NiExtraData size");
