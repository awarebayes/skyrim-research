// Type declarations for the NiAVObject translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed
// NiAVObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the member
//   functions the unit defines are declared, no data members or virtual slots.
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
#pragma once

#include <cstdint>

class bhkCollisionObject;

enum class COL_LAYER : std::uint32_t {};

class NiAVObject {
public:
    void SetCollisionLayer(COL_LAYER a_collisionLayer);
    void SetCollisionLayerAndGroup(COL_LAYER a_collisionLayer, std::uint32_t a_group);
    bhkCollisionObject* GetCollisionObject() const;
    void UpdateRigidConstraints(bool a_enable, std::uint8_t a_arg2 = 1, std::uint32_t a_arg3 = 1);
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
