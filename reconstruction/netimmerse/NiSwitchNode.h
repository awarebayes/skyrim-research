// NiSwitchNode declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-niswitchnode
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiNode.h for NiNode.
// NiSwitchNode: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// NiSwitchNode::IsEqual, NiSwitchNode::UpdateWorldBound, NiSwitchNode::SaveBinary, NiSwitchNode::AttachChild, NiSwitchNode::LoadBinary, NiSwitchNode::SetAt1, NiSwitchNode::OnVisible, NiSwitchNode::UpdateRigidDownwardPass, NiSwitchNode::UpdateDownwardPass, NiSwitchNode::UpdateSelectedDownwardPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// NiPointer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiNode.h"

template <class T> class NiPointer;

// NiChildSlots: STANDIN GUESS(low)
// Only the vtable slots the compared code calls by index are named. Slot numbers are the byte offset divided by 8; slots 0x00 to 0x26, 0x28 to 0x2B are unnamed placeholders.
// unk00 through unk26, unk28 through unk2B: GUESS(low)
class NiChildSlots
{
public:
	virtual void unk00();
	virtual void unk01();
	virtual void unk02();
	virtual void unk03();
	virtual void unk04();
	virtual void unk05();
	virtual void unk06();
	virtual void unk07();
	virtual void unk08();
	virtual void unk09();
	virtual void unk0A();
	virtual void unk0B();
	virtual void unk0C();
	virtual void unk0D();
	virtual void unk0E();
	virtual void unk0F();
	virtual void unk10();
	virtual void unk11();
	virtual void unk12();
	virtual void unk13();
	virtual void unk14();
	virtual void unk15();
	virtual void unk16();
	virtual void unk17();
	virtual void unk18();
	virtual void unk19();
	virtual void unk1A();
	virtual void unk1B();
	virtual void unk1C();
	virtual void unk1D();
	virtual void unk1E();
	virtual void unk1F();
	virtual void unk20();
	virtual void unk21();
	virtual void unk22();
	virtual void unk23();
	virtual void unk24();
	virtual void unk25();
	virtual void unk26();
	// Slot27 (0x138): GUESS(low); called with the update data by the downward passes
	virtual void Slot27(NiUpdateData& a_data);
	virtual void unk28();
	virtual void unk29();
	virtual void unk2A();
	virtual void unk2B();
	// UpdateDownwardPass (0x160): GUESS(low); as NiNode::UpdateDownwardPass in CharmedBaryon/CommonLibSSE-NG@b93280e (MIT)
	virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	// UpdateSelectedDownwardPass (0x168): GUESS(low); as NiNode::UpdateSelectedDownwardPass in CharmedBaryon/CommonLibSSE-NG@b93280e (MIT)
	virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
	// UpdateRigidDownwardPass (0x170): GUESS(low); as NiNode::UpdateRigidDownwardPass in CharmedBaryon/CommonLibSSE-NG@b93280e (MIT)
	virtual void UpdateRigidDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
};

// Stand-in helpers for the base-class bodies and the switch table; the image addresses are in
// bind-hints.json.
// NiNodeIsEqual, NiNodeSaveBinary, NiNodeLoadBinary, NiNodeAttachChild: GUESS(low); enclosing NiNode bodies
bool NiNodeIsEqual(NiNode* a_self, NiObject* a_object);
void NiNodeSaveBinary(NiNode* a_self, NiStream& a_stream);
void NiNodeLoadBinary(NiNode* a_self, NiStream& a_stream);
void NiNodeAttachChild(NiNode* a_self, NiAVObject* a_child, bool a_firstAvail);
// NiNodeSetAt1, NiNodeUpdateWorldBound, NiNodeUpdateDownwardPass, NiNodeUpdateRigidDownwardPass, NiNodeUpdateSelectedDownwardPass: GUESS(low); tail-called base bodies
void NiNodeSetAt1(NiNode* a_self, std::uint32_t a_idx, NiAVObject* a_child, NiPointer<NiAVObject>& a_childOut);
void NiNodeUpdateWorldBound(NiNode* a_self);
void NiNodeUpdateDownwardPass(NiNode* a_self, NiUpdateData& a_data, std::uint32_t a_arg2);
void NiNodeUpdateRigidDownwardPass(NiNode* a_self, NiUpdateData& a_data, std::uint32_t a_arg2);
void NiNodeUpdateSelectedDownwardPass(NiNode* a_self, NiUpdateData& a_data, std::uint32_t a_arg2);
// SwitchTableSet, SwitchTableGrow, ChildOnVisible: GUESS(low)
void SwitchTableSet(NiTArray<std::uint32_t>* a_table, std::uint32_t a_idx, std::int32_t* a_counter);
void SwitchTableGrow(NiTArray<std::uint32_t>* a_table, std::uint32_t a_size);
void ChildOnVisible(NiAVObject* a_child, NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);

// SwitchUpdateInfo: GUESS(low)
// The two-field update record OnVisible builds on the stack.
struct SwitchUpdateInfo
{
    // time: GUESS(low)
    float         time;
    // flag: GUESS(low)
    std::uint32_t flag;
};

class NiSwitchNode : public NiNode
{
public:
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xeed530
    virtual void UpdateWorldBound();  // compared: 0xeee080
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0xeed490
    virtual void AttachChild(NiAVObject* a_child, bool a_firstAvail);  // compared: 0xeed6e0
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xeed3c0
    virtual void SetAt1(std::uint32_t a_idx, NiAVObject* a_child, NiPointer<NiAVObject>& a_childOut);  // compared: 0xeedae0
    virtual void OnVisible(NiCullingProcess& a_process, std::int32_t a_alphaGroupIndex);  // compared: 0xeee100
    virtual void UpdateRigidDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xeedf20
    virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xeedc40
    virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xeedda0

    // flags128: GUESS(low); bit 0 gates the update passes, bit 1 is set by LoadBinary, bit 1 also feeds OnVisible
    std::uint16_t flags128;  // 0x128
    // activeIndex: GUESS(low); index of the one child that is shown, -1 when none
    std::int32_t activeIndex;  // 0x12C
    // time130: GUESS(low); the update time copied as a dword from the update data
    std::uint32_t time130;  // 0x130
    // counter134: GUESS(low); incremented by each pass
    std::int32_t counter134;  // 0x134
    // flagsArr: GUESS(low); NiTArray layout at 0x138 (vtable, data, capacity, free index, size, growth)
    NiTArray<std::uint32_t> flagsArr;  // 0x138
};
static_assert(sizeof(NiSwitchNode) == 0x150, "NiSwitchNode size");
