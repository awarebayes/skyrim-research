// NiBillboardNode declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-nibillboardnode
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiNode.h for NiNode.
// NiBillboardNode: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// NiBillboardNode::~NiBillboardNode, NiBillboardNode::IsEqual, NiBillboardNode::OnVisible, NiBillboardNode::LoadBinary, NiBillboardNode::SaveBinary, NiBillboardNode::UpdateWorldBound, NiBillboardNode::UpdateWorldData: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// Signature change from the community list: none. Fields of NiNode and NiAVObject are not
// recovered in the shared headers, so the compared code reads them through FieldAt in the .cpp.
// unk128, unknown12A: GUESS(low)
// BaseIsEqual, UpdateVisibleHelper: GUESS(low); callees of the compared code, declared here so the
// calls can be bound to their RVAs
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiNode.h"

class NiBillboardNode : public NiNode
{
public:
    NiBillboardNode();
    virtual ~NiBillboardNode();  // compared: 0x41cc60 (scalar deleting destructor)
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xf02dc0
    virtual void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);  // compared: 0xf041d0
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xf02ce0
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0xf02d60
    virtual void UpdateWorldBound();  // compared: 0xf02ed0
    virtual void UpdateWorldData(NiUpdateData* a_data);  // compared: 0xf02f60

    // Base-class calls the compared code makes, declared only and bound by bind-hints.json.
    // BaseIsEqual, BaseLoadBinary, BaseSaveBinary, BaseOnVisible: GUESS(low); the base-class
    // functions at 0xee17b0, 0xee1560, 0xee16e0 and 0xee2cc0.
    bool BaseIsEqual(NiObject* a_object);
    void BaseLoadBinary(NiStream& a_stream);
    void BaseSaveBinary(NiStream& a_stream);
    void BaseOnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);
    // UpdateVisibleHelper: GUESS(low); called with this and a pointer read from the culling process,
    // declared only (0xf030a0)
    void UpdateVisibleHelper(void* a_arg);

    std::uint8_t unk128[0x2];      // 128
    std::uint8_t unknown12A[0x6];  // 12A
};
static_assert(sizeof(NiBillboardNode) == 0x130, "NiBillboardNode size");
