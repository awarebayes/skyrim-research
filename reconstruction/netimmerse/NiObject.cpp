// NiObject members, build sse-steam-1-7-104.
//
// Labels: v2
// Licence: uses the name Clone from powerof3/CommonLibSSE (see the header), so this file is GPL-3.0.
// IsEqual's body is adapted from CharmedBaryon/CommonLibSSE-NG b93280e src/RE/N/NiObject.cpp
// (MIT; the notice is in NiObject.h, and the header lists every adapted body).
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names and types from the header beside this file.
// Evidence: findings/fourth-batch-selection.md.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Compared: StreamCanSkip, GetGroup, CreateClone, the constructor, Clone, IsEqual.
// RVA 0xedca00, 43 bytes: NiObject::ProcessClone
// RVA 0xedcb60, 3 bytes: NiObject::StreamCanSkip
// RVA 0xedcb90, 3 bytes: NiObject::GetGroup
// RVA 0xedc740, 4 bytes: NiObject::CreateClone
// RVA 0xedcbc0, 38 bytes: NiObject::NiObject (constructor)
// RVA 0xedc920, 68 bytes: NiObject::Clone
// RVA 0xedc7e0, 91 bytes: NiObject::IsEqual
#include "NiObject.h"

// Private stand-in used only by this translation unit; the shared header stays opaque.
// NiCloneMap, NiCloneMap::Visit: GUESS(low); names invented, the callee is bound by address through bind-hints.json
// cloneMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); name as reported by the label check, not read from NG here
// NiCloningProcess: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the map at 0x38 is declared
// unknown00: GUESS(low); padding up to the map at 0x38
class NiCloneMap
{
public:
	void Visit(NiObject** a_object, bool* a_flag, bool* a_result);
};

class NiCloningProcess
{
public:
	std::uint8_t unknown00[0x38];  // 00
	NiCloneMap   cloneMap;         // 38
};


#include <cstring>

NiObject::NiObject() {}

bool NiObject::StreamCanSkip() { return false; }

NiObjectGroup* NiObject::GetGroup() const { return nullptr; }

NiObject* NiObject::CreateClone(NiCloningProcess&) { return this; }

bool NiObject::IsEqual(NiObject* a_object)
{
	return a_object != nullptr && std::strcmp(GetRTTI()->name, a_object->GetRTTI()->name) == 0;
}

void NiObject::ProcessClone(NiCloningProcess& a_cloning)
{
	NiObject* self = this;
	bool flag = true;
	bool result;
	a_cloning.cloneMap.Visit(&self, &flag, &result);
}

NiObject* NiObject::Clone(NiCloningProcess& a_cloning)
{
	NiObject* clone = CreateClone(a_cloning);
	ProcessClone(a_cloning);
	return clone;
}
