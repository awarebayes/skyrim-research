// NiExtraData::LoadBinary, IsEqual, RegisterStreamables and ~NiExtraData, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0xef9880, 43 bytes: LoadBinary
// RVA 0xef9960, 61 bytes: IsEqual
// RVA 0xef98d0, 68 bytes: RegisterStreamables
// RVA 0xef9c50, 83 bytes: ~NiExtraData (scalar deleting destructor)
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json; all four functions are compared.
// The constructor is defined only so the vftable and the deleting destructor are emitted.
// A byte match does not verify the community method names or the original source shape.
// NiExtraData::NiExtraData: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, not compared
#include "NiExtraData.h"

NiExtraData::NiExtraData()
{
}

NiExtraData::~NiExtraData()
{
}

void NiExtraData::LoadBinary(NiStream& a_stream)
{
	NiObject::LoadBinary(a_stream);
	a_stream.LoadFixedString(name);
}

bool NiExtraData::RegisterStreamables(NiStream& a_stream)
{
	if (NiObject::RegisterStreamables(a_stream) && a_stream.RegisterFixedString(name)) {
		return true;
	}
	return false;
}

bool NiExtraData::IsEqual(NiObject* a_object)
{
	if (NiObject::IsEqual(a_object) && name._data == static_cast<NiExtraData*>(a_object)->name._data) {
		return true;
	}
	return false;
}
