// Type declarations for the NiAVObject translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT) include/RE/N/NiAVObject.h,
// NiObjectNET.h, NiCollisionObject.h, NiNode.h, NiTransform.h, NiCloningProcess.h,
// bhkCollisionObject.h and the BSTHashMap layout; AddressLibraryDatabase 0379cb6 names
// two clone-process cleanup callees and BSFixedString::Copy. Members, slots and sizes were
// checked against the listings. NiObject comes from the shared NiObject.h.
// header-gap NiRTTI: the shared NiObject.h declares only the name pointer of NiRTTI; the parent
// link at offset 8 is read through the local view NiRTTILink instead.
// Stand-ins declared here (not edited elsewhere): BSFixedString, NiPointer, NiPoint3, NiMatrix3,
// NiTransform, NiBound, NiObjectNET, NiCollisionObject, NiNode, NiExtraData, bhkCollisionObject,
// CloneHashMap, NiCloningProcess.
// Adapted code: no body in this file is copied from a community source; the only inline bodies
// are the NiPointer assignment (the usual smart-pointer shape, as in NiObjectNET.h), the
// NiCloningProcess constructor and destructor (members and order read from the listing) and
// TestBit. Bodies adapted from community sources are listed above (none);
// tools/check_origin.py reports none other above its threshold at the pinned checkouts.
// bhkCollisionObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque
// COL_LAYER: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 32-bit enum
// SetCollisionLayer, SetCollisionLayerAndGroup, GetCollisionObject, UpdateRigidConstraints: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ApplyCollisionLayer: GUESS; callee of SetCollisionLayer, bound by hint to 0x1054aa0
// CollisionLayerAndGroup: GUESS; argument pair passed by reference to the callee
// ApplyCollisionLayerAndGroup: GUESS; callee of SetCollisionLayerAndGroup, bound by hint to 0x10547e0
// FindCollisionObject: GUESS; callee of GetCollisionObject, bound by hint to 0x405d70
// EnableRigidConstraints: GUESS; callee of UpdateRigidConstraints enable path, bound by hint to 0x105c1b0
// DisableRigidConstraints: GUESS; callee of UpdateRigidConstraints disable path, bound by hint to 0x105c290
// a_arg2, a_arg3: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); purpose unknown
// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer
// _data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Copy, HasValue: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); HasValue returns an int in the image
// NiPointer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the pointer and assignment
// pointer: GUESS(low); NG names the pointer differently
// NiPoint3, NiMatrix3, NiTransform, NiBound: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layouts from the image
// operator*: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bound by hint to 0x3059a0
// IsInvalid: GUESS; callee at 0xef5c60 that decides whether the previous world transform needs a refresh, bound by hint
// NiRTTILink: GUESS; local view of NiRTTI with the parent link at offset 8
// NiExtraData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque
// NiObjectNET: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); members up to the extra-data array
// name, controllers, extra, extraDataSize, GetExtraData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// maxExtraData, unk2C: GUESS(low); the second halfword and padding to sizeof 0x30
// NiCollisionObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 25 to 29 and sceneObject
// sceneObject, Unk_25, Unk_26, Unk_27, Unk_28, Unk_29: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiAVObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 53 vftable slots in the image, sizeof 0x110
// RegisterStreamables, GetObjectByName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Clone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; signature restored from the listing
// SetName, RecalculateWorldTransform, GetBoneFromName: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission) OBSERVED; signatures restored from the listings
// UpdateControllers, PerformOp, AttachProperty, SetMaterialNeedsUpdate, SetDefaultMaterialNeedsUpdateFlag: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot placeholders so GetObjectByName lands on slot 42
// parent, parentIndex, collisionObject, local, world, previousWorld, worldBound, flags, userData, fadeAmount, lastUpdatedFrameCounter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk3C, unk109: GUESS(low); members not recovered
// unk108: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// kFlagBit9: GUESS; bit index of NG's kSaveExternalGeometryData (1 << 9), for TestBit
// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value
// NiNode: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the base class, parent->world is all the unit reads
// CloneHashMap: GUESS; the layout of NG's BSTHashMap, 0x30 bytes
// _pad00, _pad08, _capacity, _free, _good, _sentinel, _pad20, _entries: GUESS(low); the first six follow NG's BSTScatterTable member names, the last two are unobserved by the compared code
// NiCloningProcess: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout and sizeof 0x78
// cloneMap, processMap, copyType, appendChar, unk65, unk68: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// kDefaultCopyType, kDefaultAppendChar, kCloneMapSentinel, kProcessMapSentinel: GUESS; globals the constructor reads or points at, bound by address
// fUnk_CleanupCloneList1, fUnk_CleanupCloneList2: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); bound by hint to 0x20aea0 and 0x20ade0
// BSBoneMap, BSFlattenedBoneTree: STANDIN COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); callees only, written as free functions
// FindBone, FindFlattenedBone: GUESS; callees at 0xff3b30 and 0xef4c60, bound by hint
// NiRTTI_BSFlattenedBoneTree, NiRTTI_bhkCollisionObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiRTTI tables
// kBoneMapName: GUESS; fixed string at 0x332e3e0 used to look up the bone-map extra data
#pragma once

#include "NiObject.h"

#include <intrin.h>
#include <cstdint>

class bhkCollisionObject;
class NiNode;
class NiExtraData;
class NiTimeController;
class TESObjectREFR;
class NiAVObject;

enum class COL_LAYER : std::uint32_t {};

// A flag-word bit test by bit index (cookbook rule 16).
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
	return ((a_flags >> a_bit) & 1) != 0;
}

class BSFixedString {
public:
	void Copy(const BSFixedString& a_other);
	std::int32_t HasValue() const;

	const char* _data{ nullptr };  // 00
};

template <class T>
class NiPointer {
public:
	NiPointer& operator=(T* a_object)
	{
		T* old = pointer;
		if (old != a_object) {
			if (a_object) {
				// hot path: reference counts are bumped atomically
				_InterlockedIncrement(reinterpret_cast<volatile long*>(&a_object->_refCount));
			}
			pointer = a_object;
			if (old) {
				// hot path: reference counts are dropped atomically
				if (_InterlockedDecrement(reinterpret_cast<volatile long*>(&old->_refCount)) == 0) {
					old->DeleteThis();
				}
			}
		}
		return *this;
	}

	T* pointer{ nullptr };  // 00
};

class NiPoint3 {
public:
	// component-wise copy: the engine's point type copies x, y, z one by one
	NiPoint3& operator=(const NiPoint3& a_other)
	{
		x = a_other.x;
		y = a_other.y;
		z = a_other.z;
		return *this;
	}

	float x;  // 00
	float y;  // 04
	float z;  // 08
};

class NiMatrix3 {
public:
	float entry[3][3];  // 00
};

class NiTransform {
public:
	NiTransform operator*(const NiTransform& a_rhs) const;

	NiMatrix3 rotate;     // 00
	NiPoint3  translate;  // 24
	float     scale;      // 30
};
static_assert(sizeof(NiTransform) == 0x34, "NiTransform size");

class NiBound {
public:
	NiPoint3 center;  // 00
	float    radius;  // 0C
};

// Reports whether a transform slot holds no usable data yet (callee at 0xef5c60).
bool IsInvalid(const NiTransform* a_transform);

struct NiRTTILink {
	const char*       name;    // 00
	const NiRTTILink* parent;  // 08
};

extern const NiRTTI NiRTTI_BSFlattenedBoneTree;
extern const NiRTTI NiRTTI_bhkCollisionObject;
extern const BSFixedString kBoneMapName;

class NiObjectNET : public NiObject {
public:
	bool RegisterStreamables(NiStream& a_stream) override;       // 1A
	NiExtraData* GetExtraData(const BSFixedString& a_key) const;

	BSFixedString      name;           // 10
	NiTimeController*  controllers;    // 18
	NiExtraData**      extra;          // 20
	std::uint16_t      extraDataSize;  // 28
	std::uint16_t      maxExtraData;   // 2A
	std::uint32_t      unk2C;          // 2C
};
static_assert(sizeof(NiObjectNET) == 0x30, "NiObjectNET size");

class NiCollisionObject : public NiObject {
public:
	virtual void Unk_25();  // 25
	virtual void Unk_26();  // 26
	virtual void Unk_27();  // 27
	virtual void Unk_28();  // 28
	virtual void Unk_29();  // 29

	NiAVObject* sceneObject;  // 10
};

class NiAVObject : public NiObjectNET {
public:
	bool RegisterStreamables(NiStream& a_stream) override;  // 1A

	virtual void UpdateControllers();                                   // 25
	virtual void PerformOp();                                           // 26
	virtual void AttachProperty();                                      // 27
	virtual void SetMaterialNeedsUpdate();                              // 28
	virtual void SetDefaultMaterialNeedsUpdateFlag();                   // 29
	virtual NiAVObject* GetObjectByName(const BSFixedString& a_name);   // 2A

	void SetName(const BSFixedString& a_name);
	NiAVObject* Clone();
	void RecalculateWorldTransform();
	static NiAVObject* GetBoneFromName(NiAVObject* a_root, const BSFixedString& a_name, bool a_flag);

	void SetCollisionLayer(COL_LAYER a_collisionLayer);
	void SetCollisionLayerAndGroup(COL_LAYER a_collisionLayer, std::uint32_t a_group);
	bhkCollisionObject* GetCollisionObject() const;
	// out of line: the engine calls this from other translation units, it is not inlined at its users
	__declspec(noinline) bhkCollisionObject* GetCollisionObject();
	void UpdateRigidConstraints(bool a_enable, std::uint8_t a_arg2 = 1, std::uint32_t a_arg3 = 1);

	static constexpr std::uint32_t kFlagBit9 = 9;

	NiNode*                      parent;                   // 30
	std::uint32_t                parentIndex;              // 38
	std::uint32_t                unk3C;                    // 3C
	NiPointer<NiCollisionObject> collisionObject;          // 40
	NiTransform                  local;                    // 48
	NiTransform                  world;                    // 7C
	NiTransform                  previousWorld;            // B0
	NiBound                      worldBound;               // E4
	std::uint32_t                flags;                    // F4
	TESObjectREFR*               userData;                 // F8
	float                        fadeAmount;               // 100
	std::uint32_t                lastUpdatedFrameCounter;  // 104
	std::uint8_t                 unk108;                   // 108
	std::uint8_t                 unk109[7];                // 109
};
static_assert(sizeof(NiAVObject) == 0x110, "NiAVObject size");

// Only the parent link the unit reads; members after NiAVObject are not modelled.
class NiNode : public NiAVObject {
};

void ApplyCollisionLayer(NiAVObject* a_object, const COL_LAYER& a_layer);
struct CollisionLayerAndGroup {
	COL_LAYER     layer;
	std::uint32_t group;
};

void ApplyCollisionLayerAndGroup(NiAVObject* a_object, const CollisionLayerAndGroup& a_args);
void FindCollisionObject(const NiAVObject* a_object, bhkCollisionObject*& a_out);
void EnableRigidConstraints(NiAVObject* a_object, const std::uint8_t& a_arg);
void DisableRigidConstraints(NiAVObject* a_object, const std::uint8_t& a_arg);

// Clone helpers: the hash tables inside a cloning process.
class CloneHashMap {
public:
	std::uint64_t        _pad00;      // 00
	std::uint32_t        _pad08;      // 08
	std::uint32_t        _capacity;   // 0C
	std::uint32_t        _free;       // 10
	std::uint32_t        _good;       // 14
	const void*          _sentinel;   // 18
	std::uint64_t        _pad20;      // 20
	void*                _entries;    // 28
};
static_assert(sizeof(CloneHashMap) == 0x30, "CloneHashMap size");

extern const std::uint32_t kDefaultCopyType;
extern const std::uint8_t  kDefaultAppendChar;
extern const std::uint8_t  kCloneMapSentinel;
extern const std::uint8_t  kProcessMapSentinel;

// noexcept: the cloning process destructor must not throw, and the target's unwind funclet shows no extra handler
void fUnk_CleanupCloneList1(std::uint32_t* a_table) noexcept;
void fUnk_CleanupCloneList2(std::uint32_t* a_table) noexcept;

class NiCloningProcess {
public:
	NiCloningProcess()
	{
		cloneMap._capacity = 0;
		cloneMap._free = 0;
		cloneMap._good = 0;
		cloneMap._sentinel = &kCloneMapSentinel;
		cloneMap._entries = nullptr;
		processMap._capacity = 0;
		processMap._free = 0;
		processMap._good = 0;
		processMap._sentinel = &kProcessMapSentinel;
		processMap._entries = nullptr;
		copyType = kDefaultCopyType;
		appendChar = kDefaultAppendChar;
		unk68.z = 1.0f;
		unk68.y = 1.0f;
		unk68.x = 1.0f;
	}

	~NiCloningProcess()
	{
		fUnk_CleanupCloneList1(&processMap._pad08);
		fUnk_CleanupCloneList2(&cloneMap._pad08);
	}

	CloneHashMap  cloneMap;    // 00
	CloneHashMap  processMap;  // 30
	std::uint32_t copyType;    // 60
	char          appendChar;  // 64
	std::uint16_t unk65;       // 65
	NiPoint3      unk68;       // 68
};
static_assert(sizeof(NiCloningProcess) == 0x78, "NiCloningProcess size");

bool FindBone(NiExtraData* a_boneMap, const BSFixedString& a_name, NiAVObject*& a_out);
NiAVObject* FindFlattenedBone(NiAVObject* a_tree, const BSFixedString& a_name, bool a_flag);
