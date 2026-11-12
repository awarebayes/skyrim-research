// BGSMovableStatic type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/B/BGSMovableStatic.h
// and the vftables of the pinned image. TESForm and BaseFormComponent come from the shared
// header TESForm.h. TESFullName, BGSDestructibleObjectForm, TESBoundObject and TESObjectSTAT are
// stand-ins, labelled where they are declared; only class names, base
// chain, slot order and sizes are claimed.
// BGSMovableStatic: EXE_RTTI; bases in the order of the image's vftables
#pragma once

#include <cstdint>

#include "TESForm.h"

class BGSSoundDescriptorForm;

// TESFullName: STANDIN EXE_RTTI; 6 primary vftable slots
class TESFullName : public BaseFormComponent
{
public:
	// TESFullName::~TESFullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESFullName() override;  // 00
	// TESFullName::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	void InitializeDataComponent() override;  // 01
	// TESFullName::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	void ClearDataComponent() override;  // 02
	// TESFullName::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03
	// TESFullName::GetFullNameLength: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4
	virtual std::uint32_t GetFullNameLength() const;  // 04
	// TESFullName::GetFullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5
	virtual const char* GetFullName() const;  // 05

	// unk08: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk08[0x8];  // 08
};
static_assert(sizeof(TESFullName) == 0x10, "layout");

// BGSDestructibleObjectForm: STANDIN EXE_RTTI; 4 primary vftable slots
class BGSDestructibleObjectForm : public BaseFormComponent
{
public:
	// BGSDestructibleObjectForm::~BGSDestructibleObjectForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~BGSDestructibleObjectForm() override;  // 00
	// BGSDestructibleObjectForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	void InitializeDataComponent() override;  // 01
	// BGSDestructibleObjectForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	void ClearDataComponent() override;  // 02
	// BGSDestructibleObjectForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03

	// data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares DestructibleObjectData*, an opaque pointer here
	void* data;  // 08
};
static_assert(sizeof(BGSDestructibleObjectForm) == 0x10, "layout");

// TESBoundObject: STANDIN EXE_RTTI; slots beyond TESForm's are not declared
class TESBoundObject : public TESForm
{
public:
	// TESBoundObject::~TESBoundObject: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESBoundObject() override;  // 00

	// boundData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; opaque bytes, with pad2C
	std::uint8_t boundData[0x10];  // 20
};
static_assert(sizeof(TESBoundObject) == 0x30, "layout");

// TESObjectSTAT: STANDIN EXE_RTTI; NG also derives TESModelTextureSwap, folded into opaque bytes here
class TESObjectSTAT : public TESBoundObject
{
public:
	// TESObjectSTAT::~TESObjectSTAT: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESObjectSTAT() override;  // 00

	// unk30: GUESS(low); TESModelTextureSwap and data, sized from the BGSMovableStatic layout
	std::uint8_t unk30[0x50];  // 30
};
static_assert(sizeof(TESObjectSTAT) == 0x80, "layout");

// BGSMovableStatic: EXE_RTTI; bases in the order of the image's vftables
class BGSMovableStatic :
	public TESFullName,                // 00
	public BGSDestructibleObjectForm,  // 10
	public TESObjectSTAT               // 20
{
public:
	// BGSMovableStatic::BGSMovableStatic: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, defined only so the unit emits the vftables
	BGSMovableStatic();
	// BGSMovableStatic::~BGSMovableStatic: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~BGSMovableStatic() override;  // 00

	// BGSMovableStatic::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 04 of TESForm
	void InitializeData() override;  // 04

	// soundLoop: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG places it at A0
	BGSSoundDescriptorForm* soundLoop;  // A0
	// unkA8: GUESS(low); data, padA9, padAA and padAC in NG
	std::uint8_t unkA8[0x8];  // A8
};
static_assert(sizeof(BGSMovableStatic) == 0xB0, "layout");
