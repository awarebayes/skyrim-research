// NiObject members, build sse-steam-1-7-104.
//
// Labels: v2
// Licence: uses the name Clone from powerof3/CommonLibSSE (see the header), so this file is GPL-3.0.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names and types from the header beside this file.
// Evidence: findings/fourth-batch-selection.md.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Compared: StreamCanSkip, GetGroup, CreateClone, the constructor, Clone, IsEqual.
// ProcessClone (0xedca00) removed: stack slot order of the key and result locals did not match.
// RVA 0xedcb60, 3 bytes: NiObject::StreamCanSkip
// RVA 0xedcb90, 3 bytes: NiObject::GetGroup
// RVA 0xedc740, 4 bytes: NiObject::CreateClone
// RVA 0xedcbc0, 38 bytes: NiObject::NiObject (constructor)
// RVA 0xedc920, 68 bytes: NiObject::Clone
// RVA 0xedc7e0, 91 bytes: NiObject::IsEqual
#include "NiObject.h"

#include <cstring>

NiObject::NiObject() {}

bool NiObject::StreamCanSkip() { return false; }

NiObjectGroup* NiObject::GetGroup() const { return nullptr; }

NiObject* NiObject::CreateClone(NiCloningProcess&) { return this; }

bool NiObject::IsEqual(NiObject* a_object)
{
	return a_object != nullptr && std::strcmp(GetRTTI()->name, a_object->GetRTTI()->name) == 0;
}

NiObject* NiObject::Clone(NiCloningProcess& a_cloning)
{
	NiObject* clone = CreateClone(a_cloning);
	ProcessClone(a_cloning);
	return clone;
}
