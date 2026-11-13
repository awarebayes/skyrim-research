// NiSwitchNode functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-niswitchnode
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5, worker haiku-202611122349-3), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xeed530, 82 bytes: NiSwitchNode::IsEqual
//   RVA 0xeee080, 110 bytes: NiSwitchNode::UpdateWorldBound (set aside in near-miss/0xeee080.cpp)
//   RVA 0xeed490, 142 bytes: NiSwitchNode::SaveBinary (set aside in near-miss/0xeed490.cpp)
//   RVA 0xeed6e0, 143 bytes: NiSwitchNode::AttachChild (set aside in near-miss/0xeed6e0.cpp)
//   RVA 0xeed3c0, 160 bytes: NiSwitchNode::LoadBinary (set aside in near-miss/0xeed3c0.cpp)
//   RVA 0xeedae0, 161 bytes: NiSwitchNode::SetAt1 (set aside in near-miss/0xeedae0.cpp)
//   RVA 0xeee100, 170 bytes: NiSwitchNode::OnVisible (set aside in near-miss/0xeee100.cpp)
//   RVA 0xeedf20, 339 bytes: NiSwitchNode::UpdateRigidDownwardPass (set aside in near-miss/0xeedf20.cpp)
//   RVA 0xeedc40, 341 bytes: NiSwitchNode::UpdateDownwardPass (set aside in near-miss/0xeedc40.cpp)
//   RVA 0xeedda0, 363 bytes: NiSwitchNode::UpdateSelectedDownwardPass (set aside in near-miss/0xeedda0.cpp)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiSwitchNode.h"

// Update-data record accessors: the first word is the time, the second word holds the flags.
static inline std::uint32_t& UpdateWord0(NiUpdateData& a_data)
{
	return *reinterpret_cast<std::uint32_t*>(&a_data);
}

static inline std::uint32_t& UpdateWord1(NiUpdateData& a_data)
{
	return *(reinterpret_cast<std::uint32_t*>(&a_data) + 1);
}

// The shared header leaves the read pointer as void*; this view reads the same offset typed.
struct NiBinaryStreamReadSlot
{
	std::uint8_t pad[0x10];
	std::uint32_t (*readFn)(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
};

static inline NiBinaryStreamReadSlot* ReadSlot(NiBinaryStream* a_stream)
{
	return reinterpret_cast<NiBinaryStreamReadSlot*>(a_stream);
}

// The flags word is a bitfield struct in the shared header; the compared code tests it as one dword.
static inline std::uint32_t FlagsWordOf(const NiAVObject* a_object)
{
	return *reinterpret_cast<const std::uint32_t*>(&a_object->flags);
}

// Copies a child's bound in the order the image does: centre x, then the radius, then centre y and z,
// with the radius stored last. Centre words move as dwords.
static inline void CopyBoundFromChild(NiBound& a_dst, const NiBound& a_src)
{
	std::uint32_t cx = *reinterpret_cast<const std::uint32_t*>(&a_src.center.x);
	float r = a_src.radius;
	*reinterpret_cast<std::uint32_t*>(&a_dst.center.x) = cx;
	*reinterpret_cast<std::uint32_t*>(&a_dst.center.y) = *reinterpret_cast<const std::uint32_t*>(&a_src.center.y);
	*reinterpret_cast<std::uint32_t*>(&a_dst.center.z) = *reinterpret_cast<const std::uint32_t*>(&a_src.center.z);
	a_dst.radius = r;
}

// Bit 0 of the update flags, read as a byte as the image does.
static inline std::uint8_t UpdateByte1Bit0(NiUpdateData& a_data)
{
	return static_cast<std::uint8_t>(*(reinterpret_cast<std::uint8_t*>(&a_data) + 4) & 1);
}

// Child list head and link: the list head is at +0x18 of the node and the link at +0x40 of a child.
static inline NiChildSlots* ChildListHead(NiSwitchNode* a_self)
{
	return *reinterpret_cast<NiChildSlots**>(reinterpret_cast<std::uint8_t*>(a_self) + 0x18);
}

static inline NiChildSlots* ChildListNext(NiChildSlots* a_child)
{
	return *reinterpret_cast<NiChildSlots**>(reinterpret_cast<std::uint8_t*>(a_child) + 0x40);
}

// RVA 0xeed530, 82 bytes.
bool NiSwitchNode::IsEqual(NiObject* a_object)
{
	if (!NiNodeIsEqual(this, a_object)) {
		return false;
	}
	NiSwitchNode* other = static_cast<NiSwitchNode*>(a_object);
	if (activeIndex != other->activeIndex) {
		return false;
	}
	if (((static_cast<std::uint8_t>(other->flags128) ^ static_cast<std::uint8_t>(flags128)) & 1) != 0) {
		return false;
	}
	return true;
}









