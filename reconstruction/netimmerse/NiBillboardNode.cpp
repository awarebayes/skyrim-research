// NiBillboardNode functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-nibillboardnode
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (haiku-202611122349-2), starting from a tools/skeleton.py skeleton.
// Compared functions in this file:
//   RVA 0x41cc60, 52 bytes: NiBillboardNode::~NiBillboardNode
//   RVA 0xf02dc0, 68 bytes: NiBillboardNode::IsEqual
//   RVA 0xf041d0, 71 bytes: NiBillboardNode::OnVisible
//   RVA 0xf02ce0, 82 bytes: NiBillboardNode::LoadBinary
//   RVA 0xf02d60, 82 bytes: NiBillboardNode::SaveBinary
// Not in this file (not matched, kept in the unit's near-miss/ folder): RVA 0xf02ed0
// UpdateWorldBound and 0xf02f60 UpdateWorldData.
// Adapted bodies: none intended. The attempt origin check printed advice for the stream calls in
// LoadBinary and SaveBinary, similar to NiBinaryStream::write and binary_write in
// CharmedBaryon/CommonLibSSE-NG (MIT) and powerof3/CommonLibSSE (GPL-3.0); the bodies were written
// from the listing and no upstream text was copied.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiBillboardNode.h"

#include <cstdint>
#include <cstddef>

// FieldAt: GUESS(low); typed access at a fixed byte offset. The shared base headers do not recover
// the NiAVObject and NiNode fields this code reads, so the offsets are used as observed.
template <class T>
static inline T& FieldAt(void* a_base, std::size_t a_offset)
{
    return *reinterpret_cast<T*>(static_cast<std::uint8_t*>(a_base) + a_offset);
}

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiBillboardNode::NiBillboardNode()
{
}

// The scalar deleting destructor (RVA 0x41cc60, 52 bytes) is produced for the declared destructor;
// the plain destructor at RVA 0xee19d0 is bound from bind-hints.json and is not defined here, so
// the compiler calls it instead of inlining the base destructor and the vftable store (cookbook
// rule 18).

// Body done: RVA 0xf02dc0, 68 bytes, NiBillboardNode::IsEqual.
bool NiBillboardNode::IsEqual(NiObject* a_object)
{
    if (BaseIsEqual(a_object)) {
        const std::uint8_t other = static_cast<NiBillboardNode*>(a_object)->unk128[0];
        if (((other ^ unk128[0]) & 7) == 0) {
            return true;
        }
    }
    return false;
}

// Body done: RVA 0xf041d0, 71 bytes, NiBillboardNode::OnVisible.
void NiBillboardNode::OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex)
{
    if (FieldAt<std::uint8_t>(&a_process, 0x11c) != 0) {
        UpdateVisibleHelper(FieldAt<void*>(&a_process, 0x18));
    }
    BaseOnVisible(a_process, a_alphaGroupIndex);
}

// Body done: RVA 0xf02ce0, 82 bytes, NiBillboardNode::LoadBinary.
void NiBillboardNode::LoadBinary(NiStream& a_stream)
{
    BaseLoadBinary(a_stream);
    void* stream = FieldAt<void*>(&a_stream, 0x298);
    std::uint32_t count = 2;
    using ReadFn = std::int32_t (*)(void*, void*, std::uint32_t, std::uint32_t*, std::uint32_t);
    const std::int32_t read = reinterpret_cast<ReadFn>(FieldAt<void*>(stream, 0x10))(
        stream, &unk128[0], 2, &count, 1);
    FieldAt<std::uint32_t>(stream, 0x8) += static_cast<std::uint32_t>(read);
}

// Body done: RVA 0xf02d60, 82 bytes, NiBillboardNode::SaveBinary.
void NiBillboardNode::SaveBinary(NiStream& a_stream)
{
    BaseSaveBinary(a_stream);
    void* stream = FieldAt<void*>(&a_stream, 0x2a0);
    std::uint32_t count = 2;
    using WriteFn = std::int32_t (*)(void*, void*, std::uint32_t, std::uint32_t*, std::uint32_t);
    const std::int32_t written = reinterpret_cast<WriteFn>(FieldAt<void*>(stream, 0x18))(
        stream, &unk128[0], 2, &count, 1);
    FieldAt<std::uint32_t>(stream, 0x8) += static_cast<std::uint32_t>(written);
}
