// TESFullName type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESFullName.h
// and the vftables of the pinned image. BaseFormComponent and BSFixedString are stand-ins, labelled where
// they are declared; only class names, base chain, slot
// order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESFullName: EXE_RTTI; class name and base from the image RTTI
#pragma once

#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	virtual ~BaseFormComponent();  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	virtual void CopyComponent();  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer to the pooled string
// data: declared out of line, the target tail-calls it with the member address
class BSFixedString
{
public:
	// BSFixedString::data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG defines it inline, here it is the call at 0x20d100
	const char* data() const;

	// _data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); pooled string pointer
	const char* _data;  // 00
};
static_assert(sizeof(BSFixedString) == 0x8, "layout");

// TESFullName: EXE_RTTI; class name and base from the image RTTI, 6 primary vftable slots
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
	void CopyComponent() override;  // 03
	// TESFullName::GetFullNameLength: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4
	virtual std::uint32_t GetFullNameLength() const;  // 04
	// TESFullName::GetFullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5
	virtual const char* GetFullName() const;  // 05

	// fullName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	BSFixedString fullName;  // 08
};
static_assert(sizeof(TESFullName) == 0x10, "layout");
