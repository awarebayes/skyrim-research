// BSMultiBoundAABB declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsmultiboundaabb
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: inline stand-ins. The compared deleting destructor does the NiRefObject cleanup itself
// (it stores that vftable and decrements the object counter), so NiRefObject and NiObject are
// declared here with inline destructors instead of including the shared NiObject.h, whose
// out-of-line destructors would add a call.
// BSMultiBoundAABB: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSMultiBoundShape: STANDIN EXE_RTTI
// BSMultiBoundAABB::GetLength, BSMultiBoundAABB::~BSMultiBoundAABB, BSMultiBoundAABB::LoadBinary, BSMultiBoundAABB::Unk_2B, BSMultiBoundAABB::GetWithinPoint, BSMultiBoundAABB::Unk_2A, BSMultiBoundAABB::Unk_28: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Signature changes from the community list: Unk_2B, Unk_2A and Unk_28 take a pointer or a
// reference argument because the compared code reads or writes through RDX.
// unknown10, unknown18, unknown28, unknown38: GUESS(low)
// Public naming source notice:
// MIT License
//
// Copyright (c) 2018 Ryan-rsm-McKenzie
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
#pragma once

#include <intrin.h>
#include <cstdint>
#include <cstddef>

class BSDynamicTriShape;
class BSFadeNode;
class BSGeometry;
class BSLines;
class BSMultiBoundNode;
class BSSegmentedTriShape;
class BSSubIndexTriShape;
class BSTriShape;
class NiCloningProcess;
class NiControllerManager;
class NiGeometry;
class NiNode;
class NiObject;
class NiObjectGroup;
class NiParticles;
class NiRTTI;
class NiStream;
class NiSwitchNode;
class NiTriBasedGeom;
class NiTriShape;
class NiTriStrips;
class bhkAttachmentCollisionObject;
class bhkBlendCollisionObject;
class bhkLimitedHingeConstraint;
class bhkNiCollisionObject;
class bhkRigidBody;

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ~NiRefObject, DeleteThis, _refCount, _pad0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()
class NiRefObject
{
public:
    // Inline because the target inlines it into the compared deleting destructor.
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
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");

// NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Slots in NG's order, declared without bodies (only the order matters here).
// ~NiObject, GetRTTI, AsNode, AsSwitchNode, AsFadeNode, AsMultiBoundNode, AsGeometry, AsTriStrips, AsTriShape, AsSegmentedTriShape, AsSubIndexTriShape, AsDynamicTriShape, AsNiGeometry, AsNiTriBasedGeom, AsNiTriShape, AsParticlesGeom, AsLinesGeom, AsBhkNiCollisionObject, AsBhkBlendCollisionObject, AsBhkAttachmentCollisionObject, AsBhkRigidBody, AsBhkLimitedHingeConstraint, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone, PostLinkObject, StreamCanSkip, GetStreamableRTTI, GetBlockAllocationSize, GetGroup, SetGroup, AsNiControllerManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiObject : public NiRefObject
{
public:
    // Inline (empty) for the same reason as ~NiRefObject.
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

// NiPoint3: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// LoadTriple: GUESS(low); member loader called on the two NiPoint3 members, stream as second argument, declared not defined
class NiPoint3
{
public:
    void LoadTriple(NiStream& a_stream);  // 0xedbfb0 (declared only)

    float x;  // 00
    float y;  // 04
    float z;  // 08
};
static_assert(sizeof(NiPoint3) == 0xC, "NiPoint3 size");

// BSMultiBoundPlanes: GUESS(low); argument layout read by BSMultiBoundAABB::Unk_2A
// Plane, nx, ny, nz, d: GUESS(low); layout of one plane entry
struct BSMultiBoundPlanes
{
    struct Plane
    {
        float nx;  // 00
        float ny;  // 04
        float nz;  // 08
        float d;   // 0C
    };

    Plane planes[6];        // 00
    std::uint32_t mask;     // 60: bit i enables planes[i]
};
static_assert(sizeof(BSMultiBoundPlanes) == 0x64, "BSMultiBoundPlanes size");

class BSMultiBoundShape : public NiObject
{
public:
    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(BSMultiBoundShape) == 0x18, "BSMultiBoundShape size");

class BSMultiBoundAABB : public BSMultiBoundShape
{
public:
    // GetType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    virtual std::uint32_t GetType() const;
    BSMultiBoundAABB();
    virtual float GetLength();  // compared: 0x213c70
    virtual ~BSMultiBoundAABB();  // compared: 0x213ab0 (scalar deleting destructor)
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xfce870
    virtual void Unk_2B(float* a_sphere);  // compared: 0xfcf150; writes center x, y, z and radius
    virtual bool GetWithinPoint(const NiPoint3& a_pos);  // compared: 0xfcf1a0
    virtual bool Unk_2A(const BSMultiBoundPlanes& a_planes);  // compared: 0xfcf0a0
    virtual std::uint32_t Unk_28(const float* a_sphere);  // compared: 0xfceba0; x, y, z, radius in
    // unk1C: GUESS(low); box centre x, y, z
    // unk2C: GUESS(low); box half extents x, y, z
    std::uint8_t unknown18[0x4];  // 18
    NiPoint3 unk1C;               // 1C
    std::uint8_t unknown28[0x4];  // 28
    NiPoint3 unk2C;               // 2C
    std::uint8_t unknown38[0x8];  // 38
};
static_assert(sizeof(BSMultiBoundAABB) == 0x40, "BSMultiBoundAABB size");
