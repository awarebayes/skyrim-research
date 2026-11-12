// NiAVObject members and helpers, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1053280, 23 bytes: NiAVObject::SetCollisionLayer
// RVA 0x10532a0, 28 bytes: NiAVObject::SetCollisionLayerAndGroup
// RVA 0x405a50, 33 bytes: NiAVObject::GetCollisionObject
// RVA 0x105a360, 43 bytes: NiAVObject::UpdateRigidConstraints
// RVA 0xeeac80, 9 bytes: NiAVObject::SetName
// RVA 0xee0700, 70 bytes: NiAVObject::RegisterStreamables (defined here but not compared; see below)
// RVA 0x1900a0, 94 bytes: NiAVObject::GetCollisionObject (non-const overload)
// RVA 0xedc850, 199 bytes: NiAVObject::Clone (defined here but not compared; see below)
// RVA 0xfddac0, 215 bytes: NiAVObject::GetBoneFromName
// RVA 0xeec1a0, 346 bytes: NiAVObject::RecalculateWorldTransform
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from the community header; a byte match does not verify names.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// All listed functions except Clone and RegisterStreamables are compared. Clone fails the
// comparator's eh-funclet-extent check (its unwind funclet is packed against uncompared code).
// RegisterStreamables would size an existing unsized symbol-map entry, a change the map refuses
// without restaling every record. Neither has a match record. LinkObject (0xee0680) and CollectAllHavokObjects (0x1053330) were taken out of the unit as near-misses.
// Adapted code: no body in this file is copied from a community or FNV source; the bodies of
// the earlier four functions are unchanged. tools/check_origin.py reports none above its threshold.
// ApplyCollisionLayer, ApplyCollisionLayerAndGroup, FindCollisionObject: GUESS; unnamed callees, see the header
// EnableRigidConstraints, DisableRigidConstraints: GUESS; unnamed callees, see the header
// IsInvalid, FindBone, FindFlattenedBone: GUESS; unnamed callees, see the header
// NiAVObject::GetCollisionObject (non-const): COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares it const, the const overload above is the already compared one
#include "NiAVObject.h"

void NiAVObject::SetCollisionLayer(COL_LAYER a_collisionLayer)
{
    const COL_LAYER layer = a_collisionLayer;
    ApplyCollisionLayer(this, layer);
}

void NiAVObject::SetCollisionLayerAndGroup(COL_LAYER a_collisionLayer, std::uint32_t a_group)
{
    const CollisionLayerAndGroup args{ a_collisionLayer, a_group };
    ApplyCollisionLayerAndGroup(this, args);
}

bhkCollisionObject* NiAVObject::GetCollisionObject() const
{
    bhkCollisionObject* result = nullptr;
    FindCollisionObject(this, result);
    return result;
}

void NiAVObject::UpdateRigidConstraints(bool a_enable, std::uint8_t a_arg2, std::uint32_t a_arg3)
{
    if (a_enable) {
        const std::uint8_t arg = static_cast<std::uint8_t>(a_arg3);
        EnableRigidConstraints(this, arg);
    } else {
        const std::uint8_t arg = a_arg2;
        DisableRigidConstraints(this, arg);
    }
}

void NiAVObject::SetName(const BSFixedString& a_name)
{
    name.Copy(a_name);
}

bool NiAVObject::RegisterStreamables(NiStream& a_stream)
{
    if (!NiObjectNET::RegisterStreamables(a_stream)) {
        return false;
    }
    if (collisionObject.pointer) {
        collisionObject.pointer->RegisterStreamables(a_stream);
    }
    return true;
}

// Walks the runtime type chain of an object (the engine's kind-of test, inlined at its use sites).
static bool IsKindOf(const NiObject* a_object, const NiRTTI* a_type)
{
    for (const NiRTTILink* rtti = reinterpret_cast<const NiRTTILink*>(a_object->GetRTTI()); rtti; rtti = rtti->parent) {
        if (rtti == reinterpret_cast<const NiRTTILink*>(a_type)) {
            return true;
        }
    }
    return false;
}

bhkCollisionObject* NiAVObject::GetCollisionObject()
{
    NiCollisionObject* object = collisionObject.pointer;
    if (!object) {
        return nullptr;
    }
    return IsKindOf(object, &NiRTTI_bhkCollisionObject) ? reinterpret_cast<bhkCollisionObject*>(object) : nullptr;
}

NiAVObject* NiAVObject::Clone()
{
    NiCloningProcess cloning;
    NiObject* clone = CreateClone(cloning);
    ProcessClone(cloning);
    return static_cast<NiAVObject*>(clone);
}

NiAVObject* NiAVObject::GetBoneFromName(NiAVObject* a_root, const BSFixedString& a_name, bool a_flag)
{
    NiAVObject* result = nullptr;
    if (a_root) {
        if (a_name.HasValue() != 0) {
            NiExtraData* boneMap = a_root->GetExtraData(kBoneMapName);
            if (boneMap && FindBone(boneMap, a_name, result)) {
                return result;
            }
            if (a_flag) {
                return a_root->GetObjectByName(a_name);
            }
            if (a_root->GetRTTI() == &NiRTTI_BSFlattenedBoneTree) {
                return FindFlattenedBone(a_root, a_name, true);
            }
        }
        return result;
    }
    return nullptr;
}

void NiAVObject::RecalculateWorldTransform()
{
    if (parent) {
        if (TestBit(flags, kFlagBit9)) {
            world = parent->world;
        } else {
            world = parent->world * local;
        }
    } else {
        world = local;
    }
    if (IsInvalid(&previousWorld)) {
        previousWorld = world;
    }
}
