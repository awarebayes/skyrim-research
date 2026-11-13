// BSMultiBoundOBB declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s02-niobject-bsmultiboundobb
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: inline stand-ins. The compared deleting destructor does the NiRefObject cleanup itself
// (it stores that vftable and decrements the object counter), so NiRefObject and NiObject are
// declared here with inline destructors instead of including the shared NiObject.h, whose
// out-of-line destructors would add a call.
// BSMultiBoundOBB: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSMultiBoundShape, BSMultiBoundAABB: STANDIN EXE_RTTI
// BSMultiBoundOBB::GetType, BSMultiBoundOBB::SaveBinary, BSMultiBoundOBB::~BSMultiBoundOBB, BSMultiBoundOBB::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSMultiBoundOBBData::SaveBinary, BSMultiBoundOBBData::LoadBinary: GUESS(low)
// BSMultiBoundOBB::ComputeFlag: GUESS(low)
// unknown10, unknown18, unknown40, unknown64: GUESS(low)
// BSMultiBoundOBBData: GUESS(low); serialized member storage in this stand-in.
// unknown65: GUESS(low); padding after the compared flag field.
// Public declaration-source notice (CommonLibSSE-NG b93280e, MIT):
//   MIT License
//
//   Copyright (c) 2018 Ryan-rsm-McKenzie
//
//   Permission is hereby granted, free of charge, to any person obtaining a copy
//   of this software and associated documentation files (the "Software"), to deal
//   in the Software without restriction, including without limitation the rights
//   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//   copies of the Software, and to permit persons to whom the Software is
//   furnished to do so, subject to the following conditions:
//
//   The above copyright notice and this permission notice shall be included in all
//   copies or substantial portions of the Software.
//
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//   SOFTWARE.
//
#pragma once

#include <intrin.h>
#include <cstdint>

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

class BSMultiBoundShape : public NiObject
{
public:
    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(BSMultiBoundShape) == 0x18, "BSMultiBoundShape size");

class BSMultiBoundAABB : public BSMultiBoundShape
{
public:
    void SaveBinary(NiStream& a_stream) override;
    void LoadBinary(NiStream& a_stream) override;
    std::uint8_t unknown18[0x28];  // 18
};
static_assert(sizeof(BSMultiBoundAABB) == 0x40, "BSMultiBoundAABB size");

class BSMultiBoundOBBData
{
public:
    void SaveBinary(NiStream& a_stream);
    void LoadBinary(NiStream& a_stream);
    std::uint8_t padding[0x24];
};
static_assert(sizeof(BSMultiBoundOBBData) == 0x24, "BSMultiBoundOBBData size");

class BSMultiBoundOBB : public BSMultiBoundAABB
{
public:
    BSMultiBoundOBB();
    bool ComputeFlag();
    virtual std::uint32_t GetType();  // compared: 0xfcf830
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0xfcf6a0
    virtual ~BSMultiBoundOBB();  // compared: 0x213af0 (scalar deleting destructor)
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xfcf630

    BSMultiBoundOBBData unknown40;  // 40
    bool unknown64;  // 64
    std::uint8_t unknown65[0x3];  // 65
};
static_assert(sizeof(BSMultiBoundOBB) == 0x68, "BSMultiBoundOBB size");
