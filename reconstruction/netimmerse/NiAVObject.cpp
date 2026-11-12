// NiAVObject collision helpers, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1053280, 23 bytes: NiAVObject::SetCollisionLayer
// RVA 0x10532a0, 28 bytes: NiAVObject::SetCollisionLayerAndGroup
// RVA 0x405a50, 33 bytes: NiAVObject::GetCollisionObject
// RVA 0x105a360, 43 bytes: NiAVObject::UpdateRigidConstraints
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from the community header; a byte match does not verify names.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// All four functions are compared.
// ApplyCollisionLayer, ApplyCollisionLayerAndGroup, FindCollisionObject: GUESS; unnamed callees, see the header
// EnableRigidConstraints, DisableRigidConstraints: GUESS; unnamed callees, see the header
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
