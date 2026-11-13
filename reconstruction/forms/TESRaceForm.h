// TESRaceForm type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESRaceForm.h
// and the vftables of the pinned image. BaseFormComponent and TESRace are stand-ins, labelled where
// they are declared; only class names, base
// chain, slot order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESRaceForm: EXE_RTTI; class name and base from the image RTTI
#pragma once

#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	virtual ~BaseFormComponent() {}  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	virtual void CopyComponent(BaseFormComponent* a_rhs);  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");


// TESRace: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only named, never dereferenced
class TESRace;

// TESRaceForm: EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
class TESRaceForm : public BaseFormComponent
{
public:
	// TESRaceForm::TESRaceForm: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, declared so that the vftable and the deleting destructor are emitted in this unit
	TESRaceForm();
	// TESRaceForm::~TESRaceForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 00
	~TESRaceForm() override {}  // 00
	// TESRaceForm::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 01
	void InitializeDataComponent() override;  // 01
	// TESRaceForm::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 02
	void ClearDataComponent() override;  // 02
	// TESRaceForm::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 03
	void CopyComponent(BaseFormComponent* a_rhs) override;  // 03

	// race: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	TESRace* race;  // 08
};
static_assert(sizeof(TESRaceForm) == 0x10, "layout");
