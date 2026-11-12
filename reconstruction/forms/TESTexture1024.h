// TESTexture1024 type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESTexture1024.h
// and the vftables of the pinned image. BaseFormComponent and TESTexture are stand-ins, labelled where
// they are declared; only class names, base chain, slot
// order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESTexture1024: EXE_RTTI; class name and base from the image RTTI
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

// TESTexture: STANDIN EXE_RTTI; class name and base from the image RTTI
class TESTexture : public BaseFormComponent
{
public:
	// TESTexture::~TESTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESTexture() override;  // 00
	// TESTexture::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	void InitializeDataComponent() override;  // 01
	// TESTexture::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	void ClearDataComponent() override;  // 02
	// TESTexture::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	void CopyComponent() override;  // 03
	// TESTexture::GetMaxAllowedSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4
	virtual std::uint32_t GetMaxAllowedSize();  // 04
	// TESTexture::GetAsNormalFile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5
	virtual void GetAsNormalFile();  // 05
	// TESTexture::GetDefaultPath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6
	virtual void GetDefaultPath();  // 06

	// unk08: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk08[0x8];  // 08
};
static_assert(sizeof(TESTexture) == 0x10, "layout");

// TESTexture1024: EXE_RTTI; class name and base from the image RTTI
class TESTexture1024 : public TESTexture
{
public:
	// TESTexture1024::~TESTexture1024: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESTexture1024() override;  // 00
	// TESTexture1024::GetMaxAllowedSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4
	std::uint32_t GetMaxAllowedSize() override;  // 04
};
static_assert(sizeof(TESTexture1024) == 0x10, "layout");
