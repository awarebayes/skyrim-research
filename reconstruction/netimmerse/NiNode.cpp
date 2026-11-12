// NiNode: LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, OnVisible; build sse-steam-1-7-104.
//
// Labels: v2
// Licence: uses some member names from powerof3/CommonLibSSE (see the header), so this file is GPL-3.0.
// RVA 0xee1560, 58 bytes (LoadBinary); RVA 0xee15a0, 168 bytes (LinkObject);
// RVA 0xee1650, 123 bytes (RegisterStreamables); RVA 0xee16e0, 189 bytes (SaveBinary);
// RVA 0xee17b0, 161 bytes (IsEqual); RVA 0xee2cc0, 144 bytes (OnVisible).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings and
// decompiler output of the pinned image, with the class layout from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Six functions are drafted here; the constructor and UpdateDownwardPass are not.
// NiNode::LoadBinary, NiNode::LinkObject, NiNode::RegisterStreamables, NiNode::SaveBinary, NiNode::IsEqual, NiNode::OnVisible: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#include "NiNode.h"

void NiNode::LoadBinary(NiStream& a_stream)
{
	NiAVObject::LoadBinary(a_stream);
	a_stream.SkipLinkIDs();
	a_stream.SkipLinkIDs();
	flags.kNoDismemberValidity = 0;
}

void NiNode::LinkObject(NiStream& a_stream)
{
	NiAVObject::LinkObject(a_stream);

	std::uint32_t count = a_stream.ReadLinkIDCount();
	if (count) {
		SetArraySize(children, count);
		for (std::uint32_t i = 0; i < count; ++i) {
			NiAVObject* child = a_stream.ReadLinkID();
			SetAt2(i, child);
			if (child) {
				child->parentIndex = i;
			}
		}
	}

	// the stream carries a second list of links that this build reads and discards
	for (std::uint32_t skipped = a_stream.ReadLinkIDCount(); skipped; --skipped) {
		a_stream.ReadLinkID();
	}
}

bool NiNode::RegisterStreamables(NiStream& a_stream)
{
	if (!NiAVObject::RegisterStreamables(a_stream)) {
		return false;
	}
	for (std::uint32_t i = 0; i < children._freeIdx; ++i) {
		NiAVObject* child = children._data[i];
		if (child) {
			child->RegisterStreamables(a_stream);
		}
	}
	return true;
}

void NiNode::SaveBinary(NiStream& a_stream)
{
	NiAVObject::SaveBinary(a_stream);

	std::uint32_t count = children._freeIdx;
	a_stream.oStr->write(&count, 1);
	for (std::uint32_t i = 0; i < count; ++i) {
		a_stream.SaveLinkID(children._data[i]);
	}

	// trailing list count, always written as zero
	std::uint32_t zero = 0;
	a_stream.oStr->write(&zero, 1);
}

bool NiNode::IsEqual(NiObject* a_object)
{
	if (!NiAVObject::IsEqual(a_object)) {
		return false;
	}
	NiNode*       other = static_cast<NiNode*>(a_object);
	std::uint32_t count = children._freeIdx;
	if (count != other->children._freeIdx) {
		return false;
	}
	for (std::uint32_t i = 0; i < count; ++i) {
		NiAVObject* mine = children._data[i];
		NiAVObject* theirs = other->children._data[i];
		if (mine) {
			if (!theirs || !mine->IsEqual(theirs)) {
				return false;
			}
		} else if (theirs) {
			return false;
		}
	}
	return true;
}

void NiNode::OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex)
{
	// radius is tested as bits so the zero check needs no float compare
	if (worldBound.radiusBits != 0 || TestBit(FlagWord(), kAlwaysDrawBit)) {
		std::uint16_t count = children._freeIdx;
		for (std::uint16_t i = 0; i < count; ++i) {
			NiAVObject* child = children._data[i];
			if (child) {
				child->Cull(&a_process, a_alphaGroupIndex);
			}
		}
	}
}
