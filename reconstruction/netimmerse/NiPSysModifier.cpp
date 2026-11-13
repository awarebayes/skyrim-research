// NiPSysModifier member functions, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0xfa11c0, 5 bytes: SetSystemPointer
// RVA 0xfa1010, 27 bytes: LinkObject
// RVA 0xfa1040, 62 bytes: RegisterStreamables
// RVA 0xfa1140, 78 bytes: IsEqual
// RVA 0xfa1090, 170 bytes: SaveBinary
// RVA 0xfa0f40, 187 bytes: LoadBinary
// RVA 0xfa11d0, 210 bytes: ProcessClone
//
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings and
// decompiler output of the pinned image, with types from the header beside this file.
// A byte match does not verify community names or the original source shape.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// All seven functions listed above are compared.
// The stream callees that carry no community name have made-up names, labelled in the header.
// LinkObject, RegisterStreamables and ProcessClone closely parallel the FNV decompilation's
// NiPSysModifier methods (tools/check_origin.py similarity 0.92, 0.92 and 0.82): a base call and
// one stream or clone-map step in the same order, with different callee names. The lines below
// declare that parallel, found by tools/check_origin.py after drafting; they do not record a copy.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/niparticle/nipsysmodifier.cpp:53
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/niparticle/nipsysmodifier.cpp:86
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/gamebryo2.2/corelibs/niparticle/nipsysmodifier.cpp:42
#include "NiPSysModifier.h"

void NiPSysModifier::SetSystemPointer(NiParticleSystem* a_target)
{
    target = a_target;
}

void NiPSysModifier::Initialize(NiPSysData*, std::uint16_t, NiPoint3*)
{
}

void NiPSysModifier::HandleReset()
{
}

void NiPSysModifier::SetActive(bool a_active)
{
    active = a_active;
}

void NiPSysModifier::LinkObject(NiStream& a_stream)
{
    NiObject::LinkObject(a_stream);
    // the linked object is resolved later by the stream; the result is not kept here
    a_stream.ReadLinkID();
}

bool NiPSysModifier::RegisterStreamables(NiStream& a_stream)
{
    if (!NiObject::RegisterStreamables(a_stream)) {
        return false;
    }
    a_stream.RegisterFixedString(name);
    return true;
}

bool NiPSysModifier::IsEqual(NiObject* a_object)
{
    if (!NiObject::IsEqual(a_object)) {
        return false;
    }
    auto other = static_cast<NiPSysModifier*>(a_object);
    return name == other->name && order == other->order && active == other->active;
}

void NiPSysModifier::SaveBinary(NiStream& a_stream)
{
    NiObject::SaveBinary(a_stream);
    a_stream.SaveFixedString(name);
    a_stream.oStr->write(&order, 1);
    a_stream.SaveLinkID(reinterpret_cast<NiObject*>(target));
    a_stream.oStr->put(active);
}

void NiPSysModifier::LoadBinary(NiStream& a_stream)
{
    NiObject::LoadBinary(a_stream);
    if (a_stream.nifMaxVersion < 0x14010001) {
        a_stream.LoadFixedStringLegacy(name);
    } else {
        a_stream.LoadFixedString(name);
    }
    a_stream.iStr->read(&order, 1);
    a_stream.LoadLinkID();
    char isActive;
    a_stream.iStr->read(&isActive, 1);
    active = isActive != 0;
}

void NiPSysModifier::ProcessClone(NiCloningProcess& a_cloning)
{
    NiObject::ProcessClone(a_cloning);
    NiObject* found = nullptr;
    a_cloning.cloneMap.find(this, found);
    auto clone = static_cast<NiPSysModifier*>(found);
    a_cloning.cloneMap.find(reinterpret_cast<NiObject*>(target), found);
    clone->SetSystemPointer(reinterpret_cast<NiParticleSystem*>(found));
}
