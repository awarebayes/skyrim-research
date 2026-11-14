// BSTempEffect type declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Class, member and virtual names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT)
// include/RE/B/BSTempEffect.h. Layout sizes and offsets are from the image.
// Base classes: NiRefObject and NiObject are declared here as stand-ins with inline destructors,
// because the image inlines both into ~BSTempEffect and the shared netimmerse/NiObject.h declares
// them out of line (header-gap NiObject, header-gap NiRefObject).
// Adapted bodies: none in this header; BSTempEffect.cpp lists the one it has (Initialize, from
// the FNV sibling). tools/check_origin.py reports none other above its threshold at
// CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// TEMP_EFFECT_TYPE, BGSLoadGameBuffer, BGSSaveGameBuffer, TESObjectCELL: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSTempEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// lifetime, cell, age, initialized, effectID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ms_nextEffectID: GUESS(low); the counter the constructor reads and advances
#pragma once

#include <cstdint>
#include <intrin.h>

class NiAVObject;
class TESObjectCELL;

// NiRefObject, NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiRefObject: sizeof 0x10 and the counter decrement in its destructor are read from the listings
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
// _refCount, _pad0C, DeleteThis, GetRTTI, AsNode, AsSwitchNode, AsFadeNode, AsMultiBoundNode, AsGeometry, AsTriStrips, AsTriShape, AsSegmentedTriShape, AsSubIndexTriShape, AsDynamicTriShape, AsNiGeometry, AsNiTriBasedGeom, AsNiTriShape, AsParticlesGeom, AsLinesGeom: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); return types reduced to void* in this stand-in
// AsBhkNiCollisionObject, AsBhkBlendCollisionObject, AsBhkAttachmentCollisionObject, AsBhkRigidBody, AsBhkLimitedHingeConstraint, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone, PostLinkObject, StreamCanSkip: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); signatures reduced
// GetStreamableRTTI, GetBlockAllocationSize, GetGroup, SetGroup, AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); signatures reduced
class NiRefObject
{
public:
	// The image decrements the global object counter with a locked instruction.
	virtual ~NiRefObject() { _InterlockedDecrement(&ms_totalObjects); }  // 00
	virtual void DeleteThis();  // 01

	static volatile long ms_totalObjects;

	std::uint32_t _refCount;  // 08
	std::uint32_t _pad0C;     // 0C
};

class NiObject : public NiRefObject
{
public:
	NiObject();
	~NiObject() override {}  // 00
	virtual void* GetRTTI() const;  // 02
	virtual void* AsNode();  // 03
	virtual void* AsSwitchNode();  // 04
	virtual void* AsFadeNode();  // 05
	virtual void* AsMultiBoundNode();  // 06
	virtual void* AsGeometry();  // 07
	virtual void* AsTriStrips();  // 08
	virtual void* AsTriShape();  // 09
	virtual void* AsSegmentedTriShape();  // 0A
	virtual void* AsSubIndexTriShape();  // 0B
	virtual void* AsDynamicTriShape();  // 0C
	virtual void* AsNiGeometry();  // 0D
	virtual void* AsNiTriBasedGeom();  // 0E
	virtual void* AsNiTriShape();  // 0F
	virtual void* AsParticlesGeom();  // 10
	virtual void* AsLinesGeom();  // 11
	virtual void* AsBhkNiCollisionObject();  // 12
	virtual void* AsBhkBlendCollisionObject();  // 13
	virtual void* AsBhkAttachmentCollisionObject();  // 14
	virtual void* AsBhkRigidBody();  // 15
	virtual void* AsBhkLimitedHingeConstraint();  // 16
	virtual void* CreateClone(void* a_cloning);  // 17
	virtual void LoadBinary(void* a_stream);  // 18
	virtual void LinkObject(void* a_stream);  // 19
	virtual bool RegisterStreamables(void* a_stream);  // 1A
	virtual void SaveBinary(void* a_stream);  // 1B
	virtual bool IsEqual(void* a_object);  // 1C
	virtual void ProcessClone(void* a_cloning);  // 1D
	virtual void PostLinkObject(void* a_stream);  // 1E
	virtual bool StreamCanSkip();  // 1F
	virtual void* GetStreamableRTTI() const;  // 20
	virtual std::uint32_t GetBlockAllocationSize() const;  // 21
	virtual void* GetGroup() const;  // 22
	virtual void SetGroup(void* a_group);  // 23
	virtual void* AsNiControllerManager();  // 24
};
static_assert(sizeof(NiObject) == 0x10, "NiObject size");

class BGSLoadGameBuffer
{
public:
	// LoadDataEndian: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	void LoadDataEndian(void* a_data, std::uint32_t a_offset, std::uint32_t a_size);
};

class BGSSaveGameBuffer
{
public:
	// SaveDataEndian: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED
	// The image passes two more size-like values and a zero stack argument; NG declares (a_data, a_size)
	void SaveDataEndian(const void* a_data, std::uint32_t a_size, std::uint32_t a_arg3, std::uint32_t a_arg4);
};

enum class TEMP_EFFECT_TYPE
{
	kDefault = 7
};

class BSTempEffect : public NiObject
{
public:
	BSTempEffect(TESObjectCELL* a_cell, float a_lifetime);
	~BSTempEffect() override;  // 00

	virtual void             Initialize();       // 25
	virtual void             Attach();           // 26
	virtual void             Detach();           // 27
	virtual bool             Update(float a_arg1);  // 28
	virtual NiAVObject*      Get3D() const;      // 29
	virtual bool             GetManagerHandlesSaveLoad() const;  // 2A
	virtual bool             GetClearWhenCellIsUnloaded() const;  // 2B
	virtual TEMP_EFFECT_TYPE GetType() const;    // 2C
	virtual void             SaveGame(BGSSaveGameBuffer* a_buf);  // 2D
	virtual void             LoadGame(BGSLoadGameBuffer* a_buf);  // 2E
	// FinishLoadGame, IsInterfaceEffect: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	virtual void FinishLoadGame(BGSLoadGameBuffer* a_buf);
	virtual bool IsInterfaceEffect() const;

	static std::uint32_t ms_nextEffectID;

	float          lifetime;     // 10
	std::uint32_t  pad14;        // 14
	TESObjectCELL* cell;         // 18
	float          age;          // 20
	bool           initialized;  // 24
	std::uint8_t   pad25;        // 25
	std::uint16_t  pad26;        // 26
	std::uint32_t  effectID;     // 28
	std::uint32_t  pad2C;        // 2C
};
static_assert(sizeof(BSTempEffect) == 0x30, "BSTempEffect size");
